import streamlit as st
import os
from utils.export import export_results


def render():
    st.header("💾 Export Settings")

    st.subheader("Output Folder")
    output_path = st.text_input(
        "Save results to:",
        placeholder="C:/results/",
        value=st.session_state.get("output_path", "")
    )

    if output_path:
        if os.path.isdir(output_path):
            st.success(f"Folder found: {output_path}")
            st.session_state["output_path"] = output_path
        else:
            create = st.button("📁 Create folder")
            if create:
                os.makedirs(output_path, exist_ok=True)
                st.session_state["output_path"] = output_path
                st.success(f"Folder created: {output_path}")

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

    if output_path and file_name:
        preview = os.path.join(output_path, f"{file_name}.{export_format}")
        st.info(f"📄 Output file: `{preview}`")

    st.markdown("---")
    st.subheader("Export")

    # Summary of saved data
    all_results = st.session_state.get("all_results", [])
    images = st.session_state.get("images", [])
    saved_images = len(set(r["image"] for r in all_results)) if all_results else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Images sampled", f"{saved_images} / {len(images)}")
    with col2:
        st.metric("Total polygons saved", len(all_results))

    st.markdown("")

    if not all_results:
        st.warning("No data saved yet. Go to Sampling and save polygons first.")
    elif not output_path:
        st.warning("Please set an output folder above.")
    elif not file_name:
        st.warning("Please set a file name above.")
    else:
        sampling_mode = st.session_state.get("config", {}).get(
            "sampling_mode", "One colorgramme per polygon")

        if st.button("🚀 Export results", use_container_width=True):
            with st.spinner("Exporting..."):
                full_path, error = export_results(
                    all_results, sampling_mode,
                    output_path, file_name, export_format
                )
            if error:
                st.error(f"Export failed: {error}")
            else:
                st.success(f"✅ File saved: `{full_path}`")
                