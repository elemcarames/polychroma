import streamlit as st
from pathlib import Path
from PIL import Image as PILImage

from views import import_images, configuration, export_settings, sampling

# ── Page config ───────────────────────────────────────────────
favicon = PILImage.open("assets/icon.png")

st.set_page_config(
    page_title="PolyChroma",
    page_icon=favicon,
    layout="wide"
)

# ── Sidebar navigation ────────────────────────────────────────
with st.sidebar:
    logo_path = next(
        (f for f in Path("assets").glob("logo.*")
         if f.suffix.lower() in [".png", ".jpg", ".jpeg"]), None
    )
    if logo_path:
        st.image(str(logo_path), use_container_width=True)
    else:
        st.title("🎨 PolyChroma")

    st.markdown("---")

    # Custom nav menu
    nav_items = [
        ("⊞", "Import Images"),
        ("◎", "Configuration"),
        ("⊡", "Export Settings"),
        ("⬡", "Manual Sampling"),
        ("⊠", "Threshold Segmentation"),
    ]
    if "nav_tab" not in st.session_state:
        st.session_state["nav_tab"] = "Import Images"

    st.markdown("""
        <style>
        div[data-testid="stSidebarContent"] button {
            background: transparent !important;
            border: 1px solid #333333 !important;
            text-align: left !important;
            padding: 0.7rem 1rem !important;
            width: 100% !important;
            color: #CCCCCC !important;
            font-size: 1.05rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            margin-bottom: 6px !important;
            transition: all 0.2s !important;
        }
        div[data-testid="stSidebarContent"] button:hover {
            background: rgba(255, 100, 0, 0.15) !important;
            border: 1px solid #FF6400 !important;
            color: #FF6400 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    for icon, name in nav_items:
        if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
            st.session_state["nav_tab"] = name
            st.rerun()

    tab = st.session_state["nav_tab"]
# ── Routing ───────────────────────────────────────────────────
if tab == "Import Images":
    import_images.render()
elif tab == "Configuration":
    configuration.render()
elif tab == "Export Settings":
    export_settings.render()
elif tab == "Manual Sampling":
    sampling.render()
elif tab == "Threshold Segmentation":
    from views import threshold_segmentation
    threshold_segmentation.render()