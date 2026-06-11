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
        # Lista para armazenar as imagens carregadas
        images_data = []
        for uploaded_file in uploaded_files:
            try:
                # Lê o arquivo como bytes
                bytes_data = uploaded_file.getvalue()
                # Abre a imagem usando PIL (Pillow)
                img = Image.open(io.BytesIO(bytes_data))
                images_data.append({"name": uploaded_file.name, "image": img})
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

        if images_data:
            st.success(f"{len(images_data)} image(s) uploaded successfully.")
            # Armazena as imagens no session_state
            st.session_state["uploaded_images_data"] = images_data
            # Opcional: para compatibilidade com outras partes do código que esperam 'images'
            # st.session_state["images"] = [img_data["name"] for img_data in images_data]
        else:
            st.warning("No valid images were uploaded.")
    else:
        st.session_state["uploaded_images_data"] = []
        # st.session_state["images"] = []
