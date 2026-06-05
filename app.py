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

    tab = st.radio(
        "Navigation",
        options=[
            "📁 Import Images",
            "⚙️ Configuration",
            "💾 Export Settings",
            "🔬 Sampling",
            "🎯 Threshold Segmentation"
        ],
        label_visibility="collapsed"
    )

# ── Routing ───────────────────────────────────────────────────
if tab == "📁 Import Images":
    import_images.render()
elif tab == "⚙️ Configuration":
    configuration.render()
elif tab == "💾 Export Settings":
    export_settings.render()
elif tab == "🔬 Sampling":
    sampling.render()
elif tab == "🎯 Threshold Segmentation":
    from views import threshold_segmentation
    threshold_segmentation.render()