import streamlit as st
import os
import numpy as np
from PIL import Image
import colorsys


def rgb_to_hsv_array(img_array):
    """Convert RGB image array to HSV."""
    img_float = img_array.astype(float) / 255.0
    hsv = np.zeros_like(img_float)
    for i in range(img_float.shape[0]):
        for j in range(img_float.shape[1]):
            r, g, b = img_float[i, j]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            hsv[i, j] = [h * 360, s * 100, v * 100]
    return hsv


def compute_channel(img_array, channel):
    """Extract a single channel array from image."""
    if channel == "R":
        return img_array[:, :, 0].astype(float)
    elif channel == "G":
        return img_array[:, :, 1].astype(float)
    elif channel == "B":
        return img_array[:, :, 2].astype(float)
    elif channel in ["H", "S", "V"]:
        hsv = rgb_to_hsv_array(img_array)
        idx = {"H": 0, "S": 1, "V": 2}[channel]
        return hsv[:, :, idx]
    elif channel == "L":
        r = img_array[:, :, 0].astype(float)
        g = img_array[:, :, 1].astype(float)
        b = img_array[:, :, 2].astype(float)
        return 0.299 * r + 0.587 * g + 0.114 * b
    elif channel == "yR":
        r = img_array[:, :, 0].astype(float)
        g = img_array[:, :, 1].astype(float)
        b = img_array[:, :, 2].astype(float)
        total = r + g + b + 1e-6
        return r / total
    elif channel == "yG":
        r = img_array[:, :, 0].astype(float)
        g = img_array[:, :, 1].astype(float)
        b = img_array[:, :, 2].astype(float)
        total = r + g + b + 1e-6
        return g / total
    elif channel == "yB":
        r = img_array[:, :, 0].astype(float)
        g = img_array[:, :, 1].astype(float)
        b = img_array[:, :, 2].astype(float)
        total = r + g + b + 1e-6
        return b / total


CHANNEL_RANGES = {
    "R": (0, 255), "G": (0, 255), "B": (0, 255),
    "L": (0, 255),
    "H": (0, 360), "S": (0, 100), "V": (0, 100),
    "yR": (0.0, 1.0), "yG": (0.0, 1.0), "yB": (0.0, 1.0)
}


def render():
    st.header("🎯 Threshold Segmentation")

    # ── Check prerequisites ───────────────────────────────────
    if "images" not in st.session_state or not st.session_state["images"]:
        st.warning("No images loaded. Please go to Import Images first.")
        st.stop()

    images = st.session_state["images"]
    folder_path = st.session_state["folder_path"]

    # ── Image navigation ──────────────────────────────────────
    if "thresh_img_index" not in st.session_state:
        st.session_state["thresh_img_index"] = 0

    idx = st.session_state["thresh_img_index"]

    st.markdown("""
        <style>
        .img-nav-info {
            text-align: center;
            font-size: 1.3rem;
            font-weight: 700;
            padding-top: 0.4rem;
            color: white;
        }
        .img-nav-filename {
            text-align: center;
            font-size: 1rem;
            color: #FF6400;
            padding-bottom: 0.3rem;
        }
        </style>
    """, unsafe_allow_html=True)

    col_prev, col_info, col_next = st.columns([2, 3, 2])
    with col_prev:
        if st.button("⬅️  Previous", use_container_width=True, key="thresh_prev"):
            if st.session_state["thresh_img_index"] > 0:
                st.session_state["thresh_img_index"] -= 1
                st.rerun()
    with col_info:
        st.markdown(
            f'<div class="img-nav-info">Image {idx + 1} of {len(images)}</div>'
            f'<div class="img-nav-filename">{images[idx]}</div>',
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("Next  ➡️", use_container_width=True, key="thresh_next"):
            if st.session_state["thresh_img_index"] < len(images) - 1:
                st.session_state["thresh_img_index"] += 1
                st.rerun()

    # ── Load image ────────────────────────────────────────────
    idx = st.session_state["thresh_img_index"]
    img_path = os.path.join(folder_path, images[idx])
    img = Image.open(img_path).convert("RGB")
    img_array = np.array(img)
    img_w, img_h = img.size

    # ── Controls ──────────────────────────────────────────────
    st.markdown("---")
    col_ctrl1, col_ctrl2 = st.columns([1, 2])

    with col_ctrl1:
        channel = st.selectbox(
            "Channel",
            options=["R", "G", "B", "H", "S", "V", "L", "yR", "yG", "yB"],
            index=0,
            key="thresh_channel"
        )

    ch_min, ch_max = CHANNEL_RANGES[channel]
    ch_range = ch_max - ch_min
    step = 1.0 if ch_range > 2 else 0.01

    with col_ctrl2:
        thresh_range = st.slider(
            f"Threshold range — {channel}",
            min_value=float(ch_min),
            max_value=float(ch_max),
            value=(float(ch_min + ch_range * 0.3),
                   float(ch_min + ch_range * 0.8)),
            step=step,
            key="thresh_slider"
        )

    # ── Compute mask ──────────────────────────────────────────
    channel_array = compute_channel(img_array, channel)
    mask = (channel_array >= thresh_range[0]) & (channel_array <= thresh_range[1])

    # Build mask display
    mask_display = np.zeros((img_h, img_w, 3), dtype=np.uint8)
    mask_display[mask] = [255, 100, 0]
    mask_display[~mask] = [30, 30, 30]

    # ── Zoom — calculated before columns ─────────────────────
    zoom = st.slider("🔍 Zoom", min_value=20, max_value=100,
                     value=40, step=5, format="%d%%",
                     key="thresh_zoom")
    scale_pct = zoom / 100.0
    display_w = int(img_w * scale_pct)
    display_h = int(img_h * scale_pct)
    img_display = img.resize((display_w, display_h))

    # ── Two column layout ─────────────────────────────────────
    st.markdown("---")
    col_img, col_mask = st.columns([1, 1])

    
    with col_img:
        st.markdown("**Original Image**")
        st.image(img_display, use_container_width=False)

    with col_mask:
        n_pixels = int(mask.sum())
        total_pixels = img_h * img_w
        pct = n_pixels / total_pixels * 100

        st.markdown(f"**Binary Mask — {channel} ∈ [{thresh_range[0]:.1f}, {thresh_range[1]:.1f}]**")
        mask_pil = Image.fromarray(mask_display).resize((display_w, display_h))
        st.image(mask_pil, use_container_width=False)
        st.caption(f"Selected: {n_pixels:,} pixels ({pct:.1f}% of image)")

    # ── Use mask button ───────────────────────────────────────
    st.markdown("---")
    if st.button("✅ Use this mask for sampling", use_container_width=True,
                 key="thresh_use_mask"):
        from utils.color_extraction import extract_colorgramme
        config = st.session_state.get("config", {})
        config_params = config.get("params", {"R": True, "G": True, "B": True})

        colorgramme = extract_colorgramme(img_array, mask, config_params)

        result = [{
            "image": images[idx],
            "polygon": 1,
            "class": "threshold_mask",
            "colorgramme": colorgramme,
            "n_pixels": n_pixels
        }]

        st.session_state[f"results_{idx}"] = result

        all_results = []
        for i in range(len(images)):
            img_results = st.session_state.get(f"results_{i}", [])
            all_results.extend(img_results)
        st.session_state["all_results"] = all_results

        st.success(f"✅ Mask saved for {images[idx]}! "
                   f"{n_pixels:,} pixels selected. "
                   f"Go to Export Settings to download results.")