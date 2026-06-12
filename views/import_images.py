import streamlit as st
from PIL import Image
import io

def render():
    st.header("📁 Import Images")
    st.info("Upload your images (.jpg, .png, .tiff, .bmp). You can upload multiple files.")

    # Usamos st.file_uploader para permitir o upload de múltiplos arquivos
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["jpg", "jpeg", "png", "tiff", "tif", "bmp"],
        accept_multiple_files=True
    )

    if uploaded_files:
        images_data = []
        for uploaded_file in uploaded_files:
            try:
                bytes_data = uploaded_file.getvalue()
                img = Image.open(io.BytesIO(bytes_data)).convert("RGB")
                images_data.append({
                    "name": uploaded_file.name,
                    "image": img,
                    "bytes": bytes_data  # guarda os bytes também
                })
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

        if images_data:
            st.success(f"{len(images_data)} image(s) uploaded successfully.")
            st.session_state["uploaded_images_data"] = images_data
            # Opcional: para compatibilidade com outras partes do código que esperam 'images'
            # st.session_state["images"] = [img_data["name"] for img_data in images_data]
        else:
            st.warning("No valid images were uploaded.")
    else:
        st.session_state["uploaded_images_data"] = []
        # st.session_state["images"] = []
