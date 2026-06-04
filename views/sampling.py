import streamlit as st
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from streamlit_drawable_canvas import st_canvas
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


def parse_polygon_points(path_data, scale):
    points = []
    if not path_data:
        return points
    for cmd in path_data:
        if cmd[0] in ("M", "L"):
            x = cmd[1] / scale
            y = cmd[2] / scale
            points.append((x, y))
    return points


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


def render():
    st.header("🔬 Sampling")

    # ── Check prerequisites ───────────────────────────────────
    if "images" not in st.session_state or not st.session_state["images"]:
        st.warning("No images loaded. Please go to Import Images first.")
        st.stop()

    images = st.session_state["images"]
    folder_path = st.session_state["folder_path"]
    classes = st.session_state.get("classes", ["Default"])
    config = st.session_state.get("config", {})
    config_params = config.get("params", {"R": True, "G": True, "B": True})

    if "img_index" not in st.session_state:
        st.session_state["img_index"] = 0

    idx = st.session_state["img_index"]

    # ── Navigation ────────────────────────────────────────────
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
            font-size: 1.2rem !important;
            height: 3rem !important;
            font-weight: 600 !important;
        }
        canvas + div button,
        div[class*="canvas"] button {
            background-color: #444444 !important;
            border-radius: 4px !important;
            opacity: 0.7 !important;
            transition: all 0.2s !important;
        }
        canvas + div button:hover,
        div[class*="canvas"] button:hover {
            background-color: #FF6400 !important;
            opacity: 1 !important;
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
            🖱️ <b>Left click</b> — add point &nbsp;|&nbsp;
            🖱️ <b>Right click</b> — close polygon &nbsp;|&nbsp;
            ✏️ <b>Double click</b> — remove last point &nbsp;|&nbsp;
            🗑️ <b>Toolbar below</b> — undo / reset
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
            f'<div class="img-nav-info">Image {idx + 1} of {len(images)}</div>'
            f'<div class="img-nav-filename">{images[idx]}</div>',
            unsafe_allow_html=True
        )
    with col_next:
        if st.button("Next  ➡️", use_container_width=True, key=f"btn_next_{idx}"):
            if st.session_state["img_index"] < len(images) - 1:
                st.session_state["img_index"] += 1
                st.rerun()

    # ── Load image ────────────────────────────────────────────
    idx = st.session_state["img_index"]
    img_path = os.path.join(folder_path, images[idx])
    img = Image.open(img_path).convert("RGB")
    img_array = np.array(img)
    img_w, img_h = img.size

    # ── Class selector ────────────────────────────────────────
    if len(classes) > 1:
        selected_class = st.radio(
            "Active class:",
            options=classes,
            horizontal=True,
            key=f"class_radio_{idx}"
        )
    else:
        selected_class = classes[0]

    # ── Two column layout ─────────────────────────────────────
    col_canvas, col_chart = st.columns([1, 1])

    with col_canvas:
        zoom = st.slider("🔍 Zoom", min_value=20, max_value=100,
                         value=40, step=5, format="%d%%",
                         key=f"zoom_{idx}")
        scale_pct = zoom / 100.0
        canvas_w = int(img_w * scale_pct)
        canvas_h = int(img_h * scale_pct)
        scale = scale_pct
        img_display = img.resize((canvas_w, canvas_h))

        st.markdown("**Draw polygons** — left click: add point | right click: close")
        canvas_result = st_canvas(
            fill_color="rgba(255, 100, 0, 0.15)",
            stroke_width=2,
            stroke_color=CLASS_COLORS[classes.index(selected_class) % len(CLASS_COLORS)],
            background_image=img_display,
            update_streamlit=True,
            height=canvas_h,
            width=canvas_w,
            drawing_mode="polygon",
            key=f"canvas_{idx}_{zoom}"
        )

    with col_chart:
        st.markdown("**Colorgramme — average per class**")

        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            polygons = [o for o in objects if o.get("type") == "path"]

            if polygons:
                class_colorgrammes_raw = {c: [] for c in classes}

                for i, poly in enumerate(polygons):
                    path = poly.get("path", [])
                    points = parse_polygon_points(path, scale)
                    if len(points) < 3:
                        continue
                    mask = get_polygon_mask(points, img_h, img_w)
                    if mask.sum() == 0:
                        continue
                    colorgramme = extract_colorgramme(img_array, mask, config_params)
                    poly_classes = st.session_state.get(f"poly_classes_{idx}", [])
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
                        plt.close()
                else:
                    st.info("Draw a polygon to see the colorgramme.")
            else:
                st.info("Draw a polygon to see the colorgramme.")
        else:
            st.info("Draw a polygon to see the colorgramme.")

    # ── Save button ───────────────────────────────────────────
    st.markdown("---")
    col_save, col_class_save = st.columns([3, 1])

    with col_class_save:
        if len(classes) > 1:
            st.info(f"Active class: **{selected_class}**")

    with col_save:
        if st.button("💾 Save polygons for this image", key=f"btn_save_{idx}"):
            if canvas_result.json_data is None:
                st.error("No polygons drawn.")
            else:
                objects = canvas_result.json_data.get("objects", [])
                polygons = [o for o in objects if o.get("type") == "path"]

                if not polygons:
                    st.warning("No polygons found.")
                else:
                    results = []
                    for i, poly in enumerate(polygons):
                        path = poly.get("path", [])
                        points = parse_polygon_points(path, scale)
                        if len(points) < 3:
                            continue
                        mask = get_polygon_mask(points, img_h, img_w)
                        colorgramme = extract_colorgramme(img_array, mask, config_params)
                        results.append({
                            "image": images[idx],
                            "polygon": i + 1,
                            "class": selected_class,
                            "colorgramme": colorgramme,
                            "n_pixels": int(mask.sum())
                        })

                    st.session_state[f"results_{idx}"] = results

                    # Accumulate all results across images
                    all_results = []
                    for i in range(len(images)):
                        img_results = st.session_state.get(f"results_{i}", [])
                        all_results.extend(img_results)
                    st.session_state["all_results"] = all_results

                    st.success(f"✅ {len(results)} polygon(s) saved for {images[idx]}! "
                               f"Total: {len(all_results)} polygon(s) across all images.")