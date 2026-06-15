import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
from utils.color_extraction import get_polygon_mask, extract_colorgramme

CLASS_COLORS = [
    "#FF6400", "#00C8FF", "#00FF88", "#FFD700",
    "#FF00FF", "#00FFFF", "#FF4444", "#88FF00"
]

PARAM_COLORS = {
    "R": "#FF4444", "G": "#44FF44", "B": "#4444FF",
    "yR": "#FF9999", "yG": "#99FF99", "yB": "#9999FF",
    "H": "#FFD700", "S": "#FF69B4", "V": "#00CED1",
    "L": "#FFFFFF"
}

PARAM_GROUPS = {
    "RGB": ["R", "G", "B"],
    "Normalized (yRGB)": ["yR", "yG", "yB"],
    "HSV": ["H", "S", "V"],
    "Luminosity": ["L"]
}


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def average_colorgrammes(colorgramme_list):
    if not colorgramme_list:
        return {}
    avg = {}
    all_params = colorgramme_list[0].keys()
    for param in all_params:
        hists = [cg[param]["hist"] for cg in colorgramme_list if param in cg]
        edges = colorgramme_list[0][param]["edges"]
        if hists:
            avg[param] = {
                "hist": np.mean(hists, axis=0),
                "edges": edges
            }
    return avg


def plot_group(ax, group_name, params, class_colorgrammes):
    ax.set_facecolor("#0E1117")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444444")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.set_title(group_name, color="white", fontsize=10)
    ax.set_xlabel("Intensity", fontsize=8)
    ax.set_ylabel("Frequency", fontsize=8)

    has_data = False
    for class_name, colorgramme in class_colorgrammes.items():
        for param in params:
            if param in colorgramme:
                data = colorgramme[param]
                hist = data["hist"]
                edges = data["edges"]
                x = (edges[:-1] + edges[1:]) / 2
                color = PARAM_COLORS.get(param, "#FFFFFF")
                label = f"{class_name} — {param}"
                ax.plot(x, hist, color=color, linewidth=1.2,
                        alpha=0.85, label=label)
                has_data = True

    if has_data:
        ax.legend(fontsize=7, facecolor="#1E1E1E",
                  labelcolor="white", loc="upper right")
    return has_data


def draw_overlay(img_display, polygons, current_points, stroke_color):
    """Draws all closed polygons + the polygon currently being drawn onto a copy of img_display."""
    overlay = img_display.convert("RGBA").copy()
    draw = ImageDraw.Draw(overlay, "RGBA")

    # Draw closed polygons (each entry: {"points": [...], "class": ..., "color": hex})
    # Each polygon is drawn fully isolated — outline as a closed loop (not connected
    # to other polygons or to the in-progress polygon).
    for poly in polygons:
        pts = poly["points"]
        color = hex_to_rgb(poly["color"])
        if len(pts) >= 3:
            draw.polygon(pts, outline=color + (255,), fill=color + (40,), width=2)
        elif len(pts) == 2:
            draw.line(pts, fill=color + (255,), width=2)
        for p in pts:
            draw.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=color + (255,))

    # Draw current in-progress polygon — only connect points within this polygon,
    # never to previously closed polygons.
    if current_points:
        color = hex_to_rgb(stroke_color)
        if len(current_points) >= 2:
            draw.line(current_points, fill=color + (255,), width=2)
        for p in current_points:
            draw.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=color + (255,))

    return overlay.convert("RGB")


def render():
    st.header("🔬 Sampling")

    if "uploaded_images_data" not in st.session_state or not st.session_state["uploaded_images_data"]:
        st.warning("No images loaded. Please go to Import Images first.")
        st.stop()

    images_data = st.session_state["uploaded_images_data"]
    classes = st.session_state.get("classes", ["Default"])
    config = st.session_state.get("config", {})
    config_params = config.get("params", {"R": True, "G": True, "B": True})

    if "img_index" not in st.session_state:
        st.session_state["img_index"] = 0

    idx = st.session_state["img_index"]

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
        .stButton > button {
            font-size: 1.05rem !important;
            height: 2.6rem !important;
            font-weight: 600 !important;
        }
        </style>
        <div style="
            background-color: #1E1E2E;
            border-left: 3px solid #FF6400;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #CCCCCC;
            margin-bottom: 8px;
        ">
            🖱️ <b>Click</b> — add point &nbsp;|&nbsp;
            ✅ <b>Close Polygon</b> — finish current polygon &nbsp;|&nbsp;
            ↩️ <b>Undo</b> — remove last point &nbsp;|&nbsp;
            🗑️ <b>Reset</b> — clear all polygons for this image
        </div>
    """, unsafe_allow_html=True)

    col_prev, col_info, col_next = st.columns([2, 3, 2])
    with col_prev:
        if st.button("⬅️  Previous", use_container_width=True, key=f"btn_prev_{idx}"):
            if st.session_state["img_index"] > 0:
                st.session_state["img_index"] -= 1
                st.rerun()
    with col_info:
        st.markdown(
            f'<div class="img-nav-info">Image {idx + 1} of {len(images_data)}</div>'
            f'<div class="img-nav-filename">{images_data[idx]["name"]}</div>',
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("Next  ➡️", use_container_width=True, key=f"btn_next_{idx}"):
            if st.session_state["img_index"] < len(images_data) - 1:
                st.session_state["img_index"] += 1
                st.rerun()

    idx = st.session_state["img_index"]

    if "bytes" in images_data[idx]:
        img = Image.open(io.BytesIO(images_data[idx]["bytes"])).convert("RGB")
    else:
        img = images_data[idx]["image"].convert("RGB")

    img_array = np.array(img)
    img_w, img_h = img.size

    if len(classes) > 1:
        selected_class = st.radio(
            "Active class:",
            options=classes,
            horizontal=True,
            key=f"class_radio_{idx}"
        )
    else:
        selected_class = classes[0]

    stroke_color = CLASS_COLORS[classes.index(selected_class) % len(CLASS_COLORS)]

    # --- Session state for polygons on this image ---
    polygons_key = f"polygons_{idx}"
    current_key = f"current_points_{idx}"
    last_coords_key = f"last_coords_{idx}"

    if polygons_key not in st.session_state:
        st.session_state[polygons_key] = []  # list of {"points": [...], "class": ..., "color": ...}
    if current_key not in st.session_state:
        st.session_state[current_key] = []  # points of polygon being drawn
    if last_coords_key not in st.session_state:
        st.session_state[last_coords_key] = None

    polygons = st.session_state[polygons_key]
    current_points = st.session_state[current_key]

    col_canvas, col_chart = st.columns([1, 1])

    with col_canvas:
        zoom = st.slider("🔍 Zoom", min_value=20, max_value=100,
                          value=40, step=5, format="%d%%",
                          key=f"zoom_{idx}")
        scale_pct = zoom / 100.0
        canvas_w = int(img_w * scale_pct)
        canvas_h = int(img_h * scale_pct)
        scale = scale_pct

        img_display = img.resize((canvas_w, canvas_h), Image.LANCZOS)

        # Build overlay with existing polygons + current in-progress polygon
        overlay_img = draw_overlay(img_display, polygons, current_points, stroke_color)

        st.markdown("**Click to add points** — use buttons below to close / undo / reset")
        coords = streamlit_image_coordinates(
            overlay_img,
            key=f"coords_{idx}_{zoom}"
        )

        # Detect new click (compare with last recorded click)
        if coords is not None:
            click_tuple = (coords["x"], coords["y"])
            if click_tuple != st.session_state[last_coords_key]:
                st.session_state[last_coords_key] = click_tuple
                current_points.append(click_tuple)
                st.session_state[current_key] = current_points
                st.rerun()

        # Action buttons
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("✅ Close Polygon", use_container_width=True, key=f"close_{idx}"):
                if len(current_points) >= 3:
                    polygons.append({
                        "points": list(current_points),
                        "class": selected_class,
                        "color": stroke_color
                    })
                    st.session_state[polygons_key] = polygons
                    st.session_state[current_key] = []
                    st.session_state[last_coords_key] = None
                    st.rerun()
                else:
                    st.warning("Need at least 3 points to close a polygon.")
        with b2:
            if st.button("↩️ Undo Point", use_container_width=True, key=f"undo_{idx}"):
                if current_points:
                    current_points.pop()
                    st.session_state[current_key] = current_points
                    st.session_state[last_coords_key] = None
                    st.rerun()
                elif polygons:
                    polygons.pop()
                    st.session_state[polygons_key] = polygons
                    st.rerun()
        with b3:
            if st.button("🗑️ Reset", use_container_width=True, key=f"reset_{idx}"):
                st.session_state[polygons_key] = []
                st.session_state[current_key] = []
                st.session_state[last_coords_key] = None
                st.rerun()

        st.caption(f"Polygons drawn: {len(polygons)}  |  Current points: {len(current_points)}")

    # poly_classes derived directly from saved polygons (no separate tracking needed)
    poly_classes = [p["class"] for p in polygons]

    with col_chart:
        st.markdown("**Colorgramme — average per class**")

        if polygons:
            class_colorgrammes_raw = {c: [] for c in classes}

            for i, poly in enumerate(polygons):
                # Convert displayed-image coordinates back to original image coordinates
                points = [(px / scale, py / scale) for (px, py) in poly["points"]]
                if len(points) < 3:
                    continue
                mask = get_polygon_mask(points, img_h, img_w)
                if mask.sum() == 0:
                    continue
                colorgramme = extract_colorgramme(img_array, mask, config_params)

                assigned_class = poly_classes[i] if i < len(poly_classes) else selected_class

                if assigned_class in class_colorgrammes_raw:
                    class_colorgrammes_raw[assigned_class].append(colorgramme)

            class_colorgrammes_avg = {}
            for class_name, cg_list in class_colorgrammes_raw.items():
                if cg_list:
                    class_colorgrammes_avg[class_name] = average_colorgrammes(cg_list)

            if class_colorgrammes_avg:
                for group_name, params in PARAM_GROUPS.items():
                    active_params = [
                        p for p in params if config_params.get(p) or
                        (p in ["H", "S", "V"] and config_params.get("HSV"))
                    ]
                    if not active_params:
                        continue
                    fig, ax = plt.subplots(figsize=(5, 2.5))
                    fig.patch.set_facecolor("#0E1117")
                    has_data = plot_group(ax, group_name, active_params, class_colorgrammes_avg)
                    plt.tight_layout()
                    if has_data:
                        st.pyplot(fig)
                    plt.close(fig)
            else:
                st.info("Close a polygon to see the colorgramme.")
        else:
            st.info("Draw and close a polygon to see the colorgramme.")

    st.markdown("---")
    col_save, col_class_save = st.columns([3, 1])

    with col_class_save:
        if len(classes) > 1:
            st.info(f"Active class: **{selected_class}**")

    with col_save:
        if st.button("💾 Save polygons for this image", key=f"btn_save_{idx}"):
            if not polygons:
                st.warning("No polygons found.")
            else:
                results = []
                for i, poly in enumerate(polygons):
                    points = [(px / scale, py / scale) for (px, py) in poly["points"]]
                    if len(points) < 3:
                        continue
                    mask = get_polygon_mask(points, img_h, img_w)
                    colorgramme = extract_colorgramme(img_array, mask, config_params)

                    results.append({
                        "image": images_data[idx]["name"],
                        "polygon": i + 1,
                        "class": poly["class"],
                        "colorgramme": colorgramme,
                        "n_pixels": int(mask.sum())
                    })

                st.session_state[f"results_{idx}"] = results

                all_results = []
                for i in range(len(images_data)):
                    img_results = st.session_state.get(f"results_{i}", [])
                    all_results.extend(img_results)
                st.session_state["all_results"] = all_results

                st.success(f"✅ {len(results)} polygon(s) saved for {images_data[idx]['name']}! "
                           f"Total: {len(all_results)} polygon(s) across all images.")