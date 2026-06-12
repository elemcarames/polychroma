import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from utils.color_extraction import get_polygon_mask, extract_colorgramme
import io

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

    col_canvas, col_chart = st.columns([1, 1])

    # DEBUG — remover depois
    st.write(f"Image type: {type(img)}")
    st.write(f"Image mode: {img.mode}")
    st.write(f"Image size: {img.size}")
    st.image(img, caption="Debug preview", width=200)

    with col_canvas:
        zoom = st.slider("🔍 Zoom", min_value=20, max_value=100,
                         value=40, step=5, format="%d%%",
                         key=f"zoom_{idx}")
        scale_pct = zoom / 100.0
        canvas_w = int(img_w * scale_pct)
        canvas_h = int(img_h * scale_pct)
        scale = scale_pct

        img_display = img.resize((canvas_w, canvas_h), Image.LANCZOS)
        buf = io.BytesIO()
        img_display.save(buf, format="PNG")
        buf.seek(0)
        img_display = Image.open(buf).convert("RGB")

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
    # --- BLOCO DE GERENCIAMENTO DE poly_classes (AJUSTADO) ---
    poly_classes_key = f"poly_classes_{idx}"
    if poly_classes_key not in st.session_state:
        st.session_state[poly_classes_key] = []

    # Carrega a lista de classes atual para esta imagem (trabalha com uma CÓPIA)
    poly_classes = list(st.session_state[poly_classes_key]) 

    # Obtém os objetos desenhados no canvas
    current_canvas_objects = canvas_result.json_data.get("objects", []) if canvas_result.json_data else []
    # CORREÇÃO DO ERRO DE DIGITAÇÃO: 'o o' para 'o for o'
    current_num_polygons_on_canvas = len([o for o in current_canvas_objects if o.get("type") == "path"])

    # Compara o número de polígonos no canvas com o número de classes armazenadas
    if current_num_polygons_on_canvas > len(poly_classes):
        # Um novo polígono foi desenhado. Atribui a ele a classe atualmente selecionada.
        poly_classes.append(selected_class)
        st.session_state[poly_classes_key] = poly_classes # Atualiza na session_state
    elif current_num_polygons_on_canvas < len(poly_classes):
        # Um polígono foi removido. Trunca a lista.
        poly_classes = poly_classes[:current_num_polygons_on_canvas]
        st.session_state[poly_classes_key] = poly_classes # Atualiza na session_state
    # --- Fim do gerenciamento de poly_classes ---


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

                    # Usa a poly_classes já gerenciada acima para o gráfico
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
                    st.info("Draw a polygon to see the colorgramme.")
            else:
                st.info("Draw a polygon to see the colorgramme.")
        else:
            st.info("Draw a polygon to see the colorgramme.")

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

                        # Usa a poly_classes já gerenciada acima para o salvamento
                        assigned_class_for_this_polygon = poly_classes[i] if i < len(poly_classes) else selected_class

                        results.append({
                            "image": images_data[idx]["name"],
                            "polygon": i + 1,
                            "class": assigned_class_for_this_polygon, 
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