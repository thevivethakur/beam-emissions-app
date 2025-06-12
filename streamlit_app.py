import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="BEAM - Building Emissions Accounting", layout="wide")

st.sidebar.title("BEAM Navigation")
page = st.sidebar.radio("Go to", ["Project Info", "Components", "Results"])

components = [
    'Footings & Slabs', 'Foundation Walls', 'Structural Elements', 'Ext. Walls', 'Party Walls',
    'Cladding', 'Windows', 'Int. Walls', 'Floors', 'Ceilings', 'Roof', 'Garage'
]

# Placeholder data with emission factors
default_materials = pd.DataFrame({
    "Material": ["Concrete", "Steel"],
    "Category": ["Generic concrete, 35 MPa", "Reinforcement steel"],
    "Quantity": [100, 20],
    "Unit": ["m³", "tonnes"],
    "Emission Factor (kg CO2e/unit)": [100, 192.5]
})

# Calculate initial emissions
default_materials["Emissions (kg CO2e)"] = default_materials["Quantity"] * default_materials["Emission Factor (kg CO2e/unit)"]

if "component_data" not in st.session_state:
    st.session_state.component_data = {name: default_materials.copy() for name in components}

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

elif page == "Components":
    st.title("Component Materials")
    selected_component = st.selectbox("Select Component", components)

    st.markdown(f"Edit material data for **{selected_component}**")
    edited_df = st.data_editor(
        st.session_state.component_data[selected_component], 
        num_rows="dynamic", 
        use_container_width=True
    )

    # Recalculate emissions on update
    edited_df["Emissions (kg CO2e)"] = edited_df["Quantity"] * edited_df["Emission Factor (kg CO2e/unit)"]
    st.session_state.component_data[selected_component] = edited_df

    if st.button("Recalculate Emissions"):
        total_emissions = edited_df["Emissions (kg CO2e)"].sum()
        st.success(f"Total Emissions for {selected_component}: {total_emissions / 1000:.2f} t CO₂e")

elif page == "Results":
    st.title("Emissions Summary")
    all_data = pd.concat(st.session_state.component_data.values(), ignore_index=True)
    summary_df = all_data.groupby("Material")[["Emissions (kg CO2e)"]].sum().reset_index()
    summary_df["Emissions (t CO2e)"] = summary_df["Emissions (kg CO2e)"] / 1000

    total = summary_df["Emissions (t CO2e)"].sum()
    st.dataframe(summary_df[["Material", "Emissions (t CO2e)"]], use_container_width=True)
    st.metric("Total Emissions", f"{total:.1f} t CO2e")
    st.bar_chart(summary_df.set_index("Material")["Emissions (t CO2e)"])

    st.markdown("### Export Results")
    if st.button("Export to Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for name, df in st.session_state.component_data.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
        output.seek(0)
        st.download_button(
            label="Download Excel File",
            data=output,
            file_name=f"{project_id or 'BEAM'}_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
