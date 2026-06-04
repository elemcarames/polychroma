import streamlit as st


def render():
    st.header("⚙️ Configuration")

    st.subheader("Color Parameters")
    st.write("Select which parameters to extract from each polygon:")

    col1, col2, col3 = st.columns(3)
    with col1:
        param_r = st.checkbox("R (Red)", value=True)
        param_g = st.checkbox("G (Green)", value=True)
        param_b = st.checkbox("B (Blue)", value=True)
    with col2:
        param_yr = st.checkbox("yR")
        param_yg = st.checkbox("yG")
        param_yb = st.checkbox("yB")
    with col3:
        param_hsv = st.checkbox("HSV")
        param_l = st.checkbox("L (Luminosity)")

    st.markdown("---")
    st.subheader("Sampling Mode")
    sampling_mode = st.radio(
        "How to save colorgrammes:",
        options=[
            "One average colorgramme per image (all polygons merged)",
            "One colorgramme per polygon"
        ]
    )

    st.markdown("---")
    st.subheader("Class Mode")
    multi_class = st.toggle("Enable multiple classes per image", value=False)

    if multi_class:
        st.info("You will be able to assign a class label to each polygon during sampling.")
        n_classes = st.number_input("Number of classes", min_value=2, max_value=10, value=2)
        classes = []
        for i in range(int(n_classes)):
            c = st.text_input(f"Class {i+1} name", value=f"Class_{i+1}", key=f"class_{i}")
            classes.append(c)
        st.session_state["classes"] = classes
    else:
        st.session_state["classes"] = ["Default"]

    st.session_state["config"] = {
        "params": {
            "R": param_r, "G": param_g, "B": param_b,
            "yR": param_yr, "yG": param_yg, "yB": param_yb,
            "HSV": param_hsv, "L": param_l
        },
        "sampling_mode": sampling_mode,
        "multi_class": multi_class
    }

    st.success("Configuration saved automatically.")