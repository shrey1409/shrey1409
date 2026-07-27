"""
Streamlit UI for AutoVI anomaly detection.

Run:
    streamlit run app.py

Requires trained models in outputs/<category>/patchcore.pkl
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import streamlit as st
import torch
import yaml
from PIL import Image

from src.data.transforms import get_transforms
from src.features.extractor import FeatureExtractor
from src.models.patchcore import PatchCore
from src.visualization.visualizer import Visualizer
from src.inspection.structural_inspector import StructuralInspector


# ------------------------------------------------------------------
# Config & helpers
# ------------------------------------------------------------------

def load_config():
    with open("configs/config.yaml") as f:
        return yaml.safe_load(f)


@st.cache_resource
def load_model(category: str, model_cfg: dict, device: torch.device):
    """Load extractor + PatchCore for a category (cached across reruns)."""
    model_path = Path("outputs") / category / "patchcore.pkl"
    if not model_path.exists():
        return None, None

    extractor = FeatureExtractor(
        backbone_name=model_cfg["backbone"],
        layers=model_cfg["layers"],
        device=device,
    )
    patchcore = PatchCore.load(model_path)
    return extractor, patchcore


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ------------------------------------------------------------------
# Inference
# ------------------------------------------------------------------

def run_inference(image_pil: Image.Image, extractor, patchcore, cfg):
    """Return (score, anomaly_map, original_np)."""
    data_cfg = cfg["data"]
    transform_test, _ = get_transforms(
        image_size=data_cfg["image_size"],
        center_crop=data_cfg["center_crop"],
    )

    device = extractor.device
    tensor = transform_test(image_pil).unsqueeze(0).to(device)  # (1,3,H,W)

    with torch.no_grad():
        fmap = extractor(tensor)  # (1,C,h,w)
    _, C, h, w = fmap.shape
    patches = fmap.permute(0, 2, 3, 1).reshape(-1, C).cpu().numpy()
    score, amap = patchcore.predict(patches, (h, w))

    # Original image cropped to same size as anomaly detection
    crop = data_cfg["center_crop"]
    img_size = data_cfg["image_size"]
    original_np = np.array(
        image_pil.resize((img_size, img_size), Image.BICUBIC).crop(
            (
                (img_size - crop) // 2,
                (img_size - crop) // 2,
                (img_size + crop) // 2,
                (img_size + crop) // 2,
            )
        )
    )
    return score, amap, original_np


# ------------------------------------------------------------------
# Main UI
# ------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="AutoVI Anomaly Detection",
        page_icon="🔍",
        layout="wide",
    )

    cfg = load_config()
    device = get_device()

    # --- Sidebar ---
    st.sidebar.header("Settings")
    category = st.sidebar.selectbox(
        "Component category",
        cfg["data"]["categories"],
    )

    threshold = st.sidebar.slider(
        "Anomaly threshold",
        min_value=0.0, max_value=1.0, value=0.5, step=0.01,
    )
    alpha = st.sidebar.slider(
        "Heatmap opacity",
        min_value=0.1, max_value=0.9, value=0.5, step=0.05,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Model path:** `outputs/<category>/patchcore.pkl`\n\n"
        "Run `python main.py` to train models first."
    )

    # --- Title ---
    st.title(f"🔍 Anomaly Detection — {category}")

    # Load model
    extractor, patchcore = load_model(category, cfg["model"], device)

    # Tabs
    tab1, tab2 = st.tabs(["Anomaly Detection", "Structural Inspection"])

    # ------------------------------------------------------------------
    # TAB 1 - Anomaly Detection
    # ------------------------------------------------------------------
    with tab1:
        if extractor is None:
            st.error(
                f"No trained model found for **{category}**.\n"
                f"Run `python main.py --categories {category}` first."
            )
        else:
            uploaded = st.file_uploader(
                "Upload an image",
                type=["png", "jpg", "jpeg", "bmp"],
                key="anomaly_upload",
            )
            if uploaded is None:
                st.info("Upload an image to start inspection.")
            else:
                image_pil = Image.open(uploaded).convert("RGB")
                with st.spinner("Running inference ..."):
                    score, amap, original_np = run_inference(
                        image_pil, extractor, patchcore, cfg
                    )

                # Apply ROI weighting to anomaly map
                roi_cfg_cat = cfg.get("roi", {}).get(category, {})
                h, w = amap.shape
                if roi_cfg_cat.get("enabled", False):
                    orig_size = cfg["data"]["center_crop"]
                    scale_x = w / orig_size
                    scale_y = h / orig_size
                    rx = int(roi_cfg_cat["x"] * scale_x)
                    ry = int(roi_cfg_cat["y"] * scale_y)
                    rw = int(roi_cfg_cat["width"] * scale_x)
                    rh = int(roi_cfg_cat["height"] * scale_y)
                    outside_w = roi_cfg_cat.get("outside_weight", 0.0)
                    weight_map = np.full((h, w), outside_w, dtype=np.float32)
                    weight_map[ry:ry + rh, rx:rx + rw] = roi_cfg_cat.get("weight", 1.0)
                    amap = amap * weight_map
                    score = float(amap.max())

                # Load optimal threshold from evaluation metrics
                metrics_path = Path("outputs") / category / "metrics.json"
                if metrics_path.exists():
                    with open(metrics_path) as f:
                        m = json.load(f)
                    learned_threshold = m.get("img_threshold", threshold)
                else:
                    learned_threshold = threshold

                label = "anomaly" if score > learned_threshold else "normal"

                visualizer = Visualizer(alpha=alpha, contour_thresh=threshold)
                original, heatmap, overlay, bbox = visualizer.make_overlay(
                    original_np, amap, score,
                    threshold=score * threshold if label == "anomaly" else None,
                )

                if label == "anomaly":
                    st.error(f"⚠️ **ANOMALY DETECTED** — Score: `{score:.4f}`")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.subheader("Original")
                        st.image(original, use_column_width=True)
                    with col2:
                        st.subheader("Anomaly Map")
                        st.image(heatmap, use_column_width=True)
                    with col3:
                        st.subheader("Defect Location")
                        st.image(overlay, use_column_width=True)

                    if bbox is not None:
                        bx, by, bw, bh = bbox
                        st.info(
                            f"**Defect Region**\n"
                            f"Top-left: `({bx}, {by})` | "
                            f"Width: `{bw}px` | Height: `{bh}px`"
                        )

                    with st.expander("Details"):
                        st.write(f"**Image score:** {score:.6f}")
                        st.write(f"**Threshold:** {learned_threshold:.6f}")
                        st.write(f"**Anomaly map shape:** {amap.shape}")
                        st.write(f"**Max patch score:** {amap.max():.6f}")
                        st.write(f"**Mean patch score:** {amap.mean():.6f}")
                        st.write(f"**Device:** {device}")
                else:
                    st.success(f"✅ **NORMAL** — Score: `{score:.4f}`")
                    st.image(original, width=300)

    # ------------------------------------------------------------------
    # TAB 2 - Structural Inspection (engine wiring only)
    # ------------------------------------------------------------------
    with tab2:
        if category != "engine_wiring":
            st.info(
                "Structural inspection is only available for **engine_wiring**.\n"
                "Select it from the sidebar."
            )
        else:
            st.subheader("Engine Wiring Structural Inspection")
            st.caption("Checks: blue hoop presence, 2 clips present, hoop between clips")

            uploaded_struct = st.file_uploader(
                "Upload engine wiring image",
                type=["png", "jpg", "jpeg", "bmp"],
                key="struct_upload",
            )

            with st.expander("Tuning"):
                col_a, col_b = st.columns(2)
                with col_a:
                    blue_low = st.slider("Blue hue low", 80, 120, 95)
                    blue_high = st.slider("Blue hue high", 120, 140, 130)
                    min_hoop = st.slider("Min hoop area", 100, 1000, 200)
                with col_b:
                    min_clip = st.slider("Min clip area", 100, 1000, 300)
                    max_clip = st.slider("Max clip area", 1000, 10000, 5000)
                    brightness = st.slider("Clip min brightness", 150, 240, 180)

            if uploaded_struct is not None:
                img_pil = Image.open(uploaded_struct).convert("RGB")
                img = np.array(img_pil)
                H, W = img.shape[:2]

                # Scale ROI from center_crop space to full image space
                crop = cfg["data"]["center_crop"]
                roi_cfg_cat = cfg.get("roi", {}).get("engine_wiring", {})

                scaled_roi = {}
                if roi_cfg_cat.get("enabled", False):
                    scale_x = W / crop
                    scale_y = H / crop
                    scaled_roi = {
                        "enabled": True,
                        "x": int(roi_cfg_cat["x"] * scale_x),
                        "y": int(roi_cfg_cat["y"] * scale_y),
                        "width": int(roi_cfg_cat["width"] * scale_x),
                        "height": int(roi_cfg_cat["height"] * scale_y),
                        "weight": roi_cfg_cat.get("weight", 1.0),
                        "outside_weight": roi_cfg_cat.get("outside_weight", 0.0),
                    }

                inspector = StructuralInspector(
                    blue_hue_low=blue_low,
                    blue_hue_high=blue_high,
                    min_hoop_area=min_hoop,
                    min_clip_area=min_clip,
                    max_clip_area=max_clip,
                    clip_min_brightness=brightness,
                )
                with st.spinner("Running structural inspection ..."):
                    result = inspector.inspect(img, roi_cfg=scaled_roi)

                # Result banner
                if result.passed:
                    st.success("✅ **PASS** - All structural checks passed")
                else:
                    st.error("⚠️ **FAIL** - Structural anomalies detected")
                    for anomaly in result.anomalies:
                        st.write(f"- {anomaly}")

                # Annotated image
                st.image(result.annotated_image, use_column_width=True)

                # Details
                with st.expander("Details"):
                    st.write(f"**Hoop found:** {result.hoop_found}")
                    st.write(f"**Clips found:** {result.clips_found}")
                    st.write(f"**Hoop between clips:** {result.hoop_between_clips}")


if __name__ == "__main__":
    main()
