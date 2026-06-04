import streamlit as st
import os


def render():
    st.header("📁 Import Images")
    st.info("Select a folder containing your images (.jpg, .png, .tiff)")

    folder_path = st.text_input(
        "Folder path",
        placeholder="C:/my-images/",
        value=st.session_state.get("folder_path", "")
    )

    if folder_path and os.path.isdir(folder_path):
        extensions = (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp")
        images = [f for f in os.listdir(folder_path) if f.lower().endswith(extensions)]

        if images:
            st.success(f"{len(images)} image(s) found.")
            st.session_state["folder_path"] = folder_path
            st.session_state["images"] = images
        else:
            st.warning("No images found in this folder.")
    elif folder_path:
        st.error("Folder not found. Please check the path.")