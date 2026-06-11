import streamlit as st


def render():
    st.header("💾 Export Settings")



    st.markdown("---")
    st.subheader("File Format")
    export_format = st.radio(
        "Export results as:",
        options=["xlsx", "csv", "json"],
        horizontal=True
    )
    st.session_state["export_format"] = export_format

    st.markdown("---")
    st.subheader("File Name")
    file_name = st.text_input(
        "Output file name (without extension):",
        value=st.session_state.get("file_name", "polychroma_results")
    )
    st.session_state["file_name"] = file_name

    # Removemos o preview de caminho local
    # if output_path and file_name:
    #     preview = os.path.join(output_path, f"{file_name}.{export_format}")
    #     st.info(f"📄 Output file: `{preview}`")

    st.markdown("---")
    st.subheader("Export")

    # Summary of saved data
    all_results = st.session_state.get("all_results", [])
    images = st.session_state.get("uploaded_images_data", []) # Usar o novo nome da session_state
    saved_images = len(set(r["image"] for r in all_results)) if all_results else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Images sampled", f"{saved_images} / {len(images)}")
    with col2:
        st.metric("Total polygons saved", len(all_results))

    st.markdown("")

    if not all_results:
        st.warning("No data saved yet. Go to Sampling and save polygons first.")
    elif not file_name:
        st.warning("Please set a file name above.")
    else:
        sampling_mode = st.session_state.get("config", {}).get(
            "sampling_mode", "One colorgramme per polygon")


        from utils.export import export_results_as_bytes # Vamos criar essa nova função ou adaptar a existente

        if st.button("🚀 Prepare for Download", use_container_width=True):
            with st.spinner("Preparing data for download..."):
                try:
                    # Chama a função que agora retorna os bytes do arquivo
                    file_bytes = export_results_as_bytes(
                        all_results, sampling_mode, file_name, export_format
                    )
                    if file_bytes:
                        st.success("Data ready for download!")
                        st.download_button(
                            label=f"⬇️ Download {file_name}.{export_format}",
                            data=file_bytes,
                            file_name=f"{file_name}.{export_format}",
                            mime=f"application/{export_format}" if export_format != "xlsx" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.error("Failed to prepare data for download.")
                except Exception as e:
                    st.error(f"Error preparing data: {e}")
