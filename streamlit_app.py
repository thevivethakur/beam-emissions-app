
import streamlit as st
import pandas as pd

st.set_page_config(page_title="BEAM - Building Emissions Accounting", layout="wide")

st.sidebar.title("BEAM Navigation")
page = st.sidebar.radio("Go to", ["Project Info", "Footings & Slabs", "Foundation Walls", "Structural Elements", "Results"])

default_materials = pd.DataFrame({
    "Material": ["Concrete", "Steel"],
    "Category": ["Generic concrete, 35 MPa", "Reinforcement steel"],
    "Quantity": [100, 20],
    "Unit": ["m³", "tonnes"],
    "Emissions (kg CO2e)": [11229, 3850]
})

if "materials" not in st.session_state:
    st.session_state.materials = default_materials.copy()

if page == "Project Info":
    st.title("Project Information")
    with st.form("project_form"):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name", "Example Project")
            building_type = st.selectbox("Building Type", ["Office", "Residential", "School", "Hospital"])
        with col2:
            floor_area = st.number_input("Floor Area (m²)", min_value=0, value=5000)
            project_id = st.text_input("Project ID", "AUTO123")
        submitted = st.form_submit_button("Save Project Info")
        if submitted:
            st.success("Project information saved.")

elif page in ["Footings & Slabs", "Foundation Walls", "Structural Elements"]:
    st.title(page)
    st.markdown("Use the table below to add or edit materials for this section.")
    edited_df = st.data_editor(st.session_state.materials, num_rows="dynamic", use_container_width=True)
    st.session_state.materials = edited_df

    if st.button("Recalculate Emissions"):
        total_emissions = edited_df["Emissions (kg CO2e)"].sum()
        st.success(f"Total Emissions for {page}: {total_emissions / 1000:.2f} t CO₂e")

elif page == "Results":
    st.title("Emissions Summary")
    materials = st.session_state.materials
    summary_df = materials.groupby("Material")[["Emissions (kg CO2e)"]].sum().reset_index()
    summary_df["Emissions (t CO2e)"] = summary_df["Emissions (kg CO2e)"] / 1000

    total = summary_df["Emissions (t CO2e)"].sum()
    st.dataframe(summary_df[["Material", "Emissions (t CO2e)"]], use_container_width=True)
    st.metric("Total Emissions", f"{total:.1f} t CO2e")
    st.bar_chart(summary_df.set_index("Material")["Emissions (t CO2e)"])
