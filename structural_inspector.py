"""
Engine wiring structural inspector.

Checks:
1. Two metal clips are present
2. Blue hoop is present
3. Blue hoop is positioned between the two clips
"""
import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class InspectionResult:
    passed: bool
    anomalies: List[str]
    hoop_found: bool
    clips_found: int
    hoop_between_clips: bool
    annotated_image: np.ndarray


class StructuralInspector:

    def __init__(
        self,
        blue_hue_low=95,
        blue_hue_high=130,
        min_hoop_area=200,
        min_clip_area=300,
        max_clip_area=5000,
        clip_min_brightness=180,
    ):
        self.blue_hue_low = blue_hue_low
        self.blue_hue_high = blue_hue_high
        self.min_hoop_area = min_hoop_area
        self.min_clip_area = min_clip_area
        self.max_clip_area = max_clip_area
        self.clip_min_brightness = clip_min_brightness

    # ------------------------------------------------------------------
    def inspect(
        self,
        image: np.ndarray,
        roi_cfg: dict = None,
    ) -> InspectionResult:

        annotated = image.copy()
        anomalies = []

        # Extract ROI region for detection
        if roi_cfg and roi_cfg.get("enabled", False):
            x = roi_cfg["x"]
            y = roi_cfg["y"]
            rw = roi_cfg["width"]
            rh = roi_cfg["height"]
            region = image[y:y + rh, x:x + rw]

            # Draw yellow ROI box on full image
            cv2.rectangle(annotated, (x, y), (x + rw, y + rh), (0, 255, 255), 2)
            cv2.putText(annotated, "ROI", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        else:
            region = image
            x, y = 0, 0

        # --- Step 1: Detect blue hoop ---
        hoop_contour = self._detect_blue_hoop(region)
        hoop_found = hoop_contour is not None

        if not hoop_found:
            anomalies.append("Blue hoop not found")
        else:
            shifted = hoop_contour + np.array([x, y])
            cv2.drawContours(annotated, [shifted], -1, (255, 0, 0), 2)
            M = cv2.moments(shifted)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(annotated, "Blue Hoop", (cx - 30, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # --- Step 2: Detect metal clips ---
        clips = self._detect_clips(region, hoop_contour)
        clips_found = len(clips)

        if clips_found < 2:
            anomalies.append(f"Expected 2 clips, found {clips_found}")

        for i, (cx2, cy2, cw, ch) in enumerate(clips):
            cv2.rectangle(annotated,
                          (cx2 + x, cy2 + y),
                          (cx2 + x + cw, cy2 + y + ch),
                          (0, 165, 255), 2)
            cv2.putText(annotated, f"Clip {i + 1}", (cx2 + x, cy2 + y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        # --- Step 3: Check hoop is between clips ---
        hoop_between = False
        if hoop_found and clips_found >= 2:
            hoop_between = self._is_hoop_between_clips(
                hoop_contour, clips
            )
            if not hoop_between:
                anomalies.append("Blue hoop is not between the two clips")

        passed = len(anomalies) == 0

        # Result banner
        color = (0, 200, 0) if passed else (0, 0, 255)
        status = "PASS" if passed else "FAIL"
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 35), color, -1)
        cv2.putText(annotated, status, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        return InspectionResult(
            passed=passed,
            anomalies=anomalies,
            hoop_found=hoop_found,
            clips_found=clips_found,
            hoop_between_clips=hoop_between,
            annotated_image=annotated,
        )

    # ------------------------------------------------------------------
    def _detect_blue_hoop(
        self, region: np.ndarray
    ) -> Optional[np.ndarray]:
        """Detect blue hoop using HSV color segmentation."""
        hsv = cv2.cvtColor(region, cv2.COLOR_RGB2HSV)
        lower = np.array([self.blue_hue_low, 80, 50])
        upper = np.array([self.blue_hue_high, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        valid = [c for c in contours
                 if cv2.contourArea(c) > self.min_hoop_area]
        if not valid:
            return None
        return max(valid, key=cv2.contourArea)

    # ------------------------------------------------------------------
    def _detect_clips(
        self,
        region: np.ndarray,
        hoop_contour: Optional[np.ndarray],
    ) -> List[Tuple[int, int, int, int]]:
        hsv = cv2.cvtColor(region, cv2.COLOR_RGB2HSV)

        # Silver/metallic = low saturation, high brightness
        lower_silver = np.array([0, 0, self.clip_min_brightness])  # raise brightness threshold
        upper_silver = np.array([180, 40, 255])                    # lower saturation threshold
        mask = cv2.inRange(hsv, lower_silver, upper_silver)

        # Remove blue hoop region
        if hoop_contour is not None:
            hoop_mask = np.zeros(region.shape[:2], dtype=np.uint8)
            cv2.drawContours(hoop_mask, [hoop_contour], -1, 255, -1)
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(hoop_mask))

        kernel = np.ones((3, 3), np.uint8)  # smaller kernel - less dilation
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        clips = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self.min_clip_area:
                continue
            if area > self.max_clip_area:   # reduce max area - clips are small
                continue

            x, y, w, h = cv2.boundingRect(c)
            aspect = w / (h + 1e-5)

            # clips are roughly square
            if 0.5 < aspect < 2.0:   # tighter aspect ratio
                clips.append((x, y, w, h))

        # Merge overlapping boxes - nearby detections are the same clip
        clips = self._merge_overlapping_boxes(clips, overlap_thresh=0.3)

        clips.sort(key=lambda b: b[0])  # sort left to right
        clips.sort(key=lambda b: b[2] * b[3], reverse=True)
        return clips[:2]

    # ------------------------------------------------------------------
    def _merge_overlapping_boxes(
        self,
        boxes: List[Tuple[int, int, int, int]],
        overlap_thresh: float = 0.3,
    ) -> List[Tuple[int, int, int, int]]:
        """Merge boxes that overlap significantly into one box."""
        if not boxes:
            return []

        merged = []
        used = [False] * len(boxes)

        for i, (x1, y1, w1, h1) in enumerate(boxes):
            if used[i]:
                continue
            group = [(x1, y1, w1, h1)]
            for j, (x2, y2, w2, h2) in enumerate(boxes):
                if i == j or used[j]:
                    continue
                # Check overlap
                ix = max(x1, x2)
                iy = max(y1, y2)
                iw = min(x1 + w1, x2 + w2) - ix
                ih = min(y1 + h1, y2 + h2) - iy
                if iw > 0 and ih > 0:
                    overlap = (iw * ih) / min(w1 * h1, w2 * h2)
                    if overlap > overlap_thresh:
                        group.append((x2, y2, w2, h2))
                        used[j] = True

            # Merge group into one bounding box
            gx = min(b[0] for b in group)
            gy = min(b[1] for b in group)
            gw = max(b[0] + b[2] for b in group) - gx
            gh = max(b[1] + b[3] for b in group) - gy
            merged.append((gx, gy, gw, gh))
            used[i] = True

        return merged

    # ------------------------------------------------------------------
    def _is_hoop_between_clips(
        self,
        hoop_contour: np.ndarray,
        clips: List[Tuple[int, int, int, int]],
    ) -> bool:
        """
        Check if hoop centre x lies strictly between the right edge
        of left clip and left edge of right clip.
        """
        if len(clips) < 2:
            return False

        M = cv2.moments(hoop_contour)
        if M["m00"] == 0:
            return False

        hoop_cx = int(M["m10"] / M["m00"])
        hoop_cy = int(M["m01"] / M["m00"])

        # Sort clips left to right by their centre x
        clips_sorted = sorted(clips, key=lambda c: c[0] + c[2] // 2)
        left_clip = clips_sorted[0]
        right_clip = clips_sorted[1]

        left_clip_right_edge = left_clip[0] + left_clip[2]
        right_clip_left_edge = right_clip[0]

        print(f"  Hoop centre x: {hoop_cx}")
        print(f"  Left clip right edge: {left_clip_right_edge}")
        print(f"  Right clip left edge: {right_clip_left_edge}")

        return left_clip_right_edge < hoop_cx < right_clip_left_edge
