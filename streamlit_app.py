import streamlit as st
import pandas as pd
from io import BytesIO
from streamlit_chat import message

st.set_page_config(page_title="BEAM - Emissions App", layout="wide", page_icon="🏗️")

st.markdown("""<h1 style='text-align: center; color: #3f51b5;'>🏗️ BEAM - Building Emissions Accounting Model</h1>""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://upload.wikedia.org/wikipedia/commons/thumb/3/38/Streamlit_logo_mark.svg/2048px-Streamlit_logo_mark.svg.png", width=60)
    page = st.radio("Navigation", ["Project Info", "Components", "Results", "AI Assistant"])

components = [
    'Footings & Slabs', 'Foundation Walls', 'Structural Elements', 'Ext. Walls', 'Party Walls',
    'Cladding', 'Windows', 'Int. Walls', 'Floors', 'Ceilings', 'Roof', 'Garage'
]

default_materials = pd.DataFrame({
    "Material": ["Concrete", "Steel"],
    "Category": ["Generic concrete, 35 MPa", "Reinforcement steel"],
    "Quantity": [100, 20],
    "Unit": ["m³", "tonnes"],
    "Emission Factor (kg CO2e/unit)": [100, 192.5]
})
default_materials["Emissions (kg CO2e)"] = default_materials["Quantity"] * default_materials["Emission Factor (kg CO2e/unit)"]

if "component_data" not in st.session_state:
    st.session_state.component_data = {name: default_materials.copy() for name in components}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if page == "Project Info":
    st.subheader("Project Information")
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
            st.success("Project information saved successfully.")

elif page == "Components":
    st.subheader("Component Materials")
    selected_component = st.selectbox("Select Component", components)
    edited_df = st.data_editor(
        st.session_state.component_data[selected_component],
        num_rows="dynamic",
        use_container_width=True
    )
    edited_df["Emissions (kg CO2e)"] = edited_df["Quantity"] * edited_df["Emission Factor (kg CO2e/unit)"]
    st.session_state.component_data[selected_component] = edited_df

    if st.button("Recalculate Emissions"):
        total = edited_df["Emissions (kg CO2e)"].sum()
        st.success(f"Emissions for {selected_component}: {total / 1000:.2f} t CO₂e")

elif page == "Results":
    st.subheader("Emissions Summary")
    all_data = pd.concat(st.session_state.component_data.values(), ignore_index=True)
    summary_df = all_data.groupby("Material")[["Emissions (kg CO2e)"]].sum().reset_index()
    summary_df["Emissions (t CO2e)"] = summary_df["Emissions (kg CO2e)"] / 1000
    total = summary_df["Emissions (t CO2e)"].sum()
    st.metric("Total Emissions", f"{total:.1f} t CO2e")
    st.dataframe(summary_df[["Material", "Emissions (t CO2e)"]], use_container_width=True)
    st.bar_chart(summary_df.set_index("Material")["Emissions (t CO2e)"])

    st.markdown("### Export Results")
    if st.button("Export to Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for name, df in st.session_state.component_data.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
        output.seek(0)
        st.download_button("Download Excel", output, file_name="beam_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif page == "AI Assistant":
    st.subheader("Ask BEAM Assistant 🤖")
    prompt = st.text_input("Ask a question about materials, emissions, or low-carbon alternatives:")

    if prompt:
        if "concrete" in prompt.lower():
            response = "Concrete is highly emissive due to cement. Consider low-carbon alternatives like fly ash concrete or geopolymer cement."
        elif "summary" in prompt.lower():
            total = sum(df["Emissions (kg CO2e)"].sum() for df in st.session_state.component_data.values()) / 1000
            response = f"Your total project emissions are approximately {total:.2f} t CO₂e."
        else:
            response = "This is a demo assistant. For full GPT capabilities, integrate with OpenAI API."
        st.session_state.chat_history.append((prompt, response))

    for i, (user, bot) in enumerate(st.session_state.chat_history):
        message(user, is_user=True, key=f"user_{i}")
        message(bot, key=f"bot_{i}")
