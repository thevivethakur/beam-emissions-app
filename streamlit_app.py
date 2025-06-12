import streamlit as st
import pandas as pd
from io import BytesIO
from streamlit_chat import message
from openai import OpenAI
import os
import pdfplumber
from PIL import Image

st.set_page_config(page_title="BEAM - Emissions App", layout="wide")

# Sidebar with plain text
with st.sidebar:
    st.title("BEAM")
    page = st.radio("Navigation", ["Project Info", "Components", "Results", "AI Assistant"])

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY"))

components = ['Footings & Slabs', 'Foundation Walls', 'Structural Elements', 'Ext. Walls', 'Party Walls',
              'Cladding', 'Windows', 'Int. Walls', 'Floors', 'Ceilings', 'Roof', 'Garage']

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
if "uploaded_content" not in st.session_state:
    st.session_state.uploaded_content = ""

if page == "Project Info":
    st.header("Project Information")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Project Name", "Example Project")
        st.selectbox("Building Type", ["Office", "Residential", "School", "Hospital"])
    with col2:
        st.number_input("Floor Area (m²)", min_value=0, value=5000)
        st.text_input("Project ID", "AUTO123")

elif page == "Components":
    st.header("Component Materials")
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
    st.header("Emissions Summary")
    all_data = pd.concat(st.session_state.component_data.values(), ignore_index=True)
    summary_df = all_data.groupby("Material")[["Emissions (kg CO2e)"]].sum().reset_index()
    summary_df["Emissions (t CO2e)"] = summary_df["Emissions (kg CO2e)"] / 1000
    total = summary_df["Emissions (t CO2e)"].sum()
    st.metric("Total Emissions", f"{total:.1f} t CO2e")
    st.dataframe(summary_df[["Material", "Emissions (t CO2e)"]], use_container_width=True)
    st.bar_chart(summary_df.set_index("Material")["Emissions (t CO2e)"])

    if st.button("Download Excel Report"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for name, df in st.session_state.component_data.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
        output.seek(0)
        st.download_button("Download Excel", output, file_name="beam_results.xlsx")

elif page == "AI Assistant":
    st.header("BEAM Assistant")
    uploaded_file = st.file_uploader("Upload a design file (PDF or Image)", type=["pdf", "png", "jpg"])
    upload_text = ""
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                pages = [page.extract_text() for page in pdf.pages]
                upload_text = "\n".join(filter(None, pages))
        elif uploaded_file.type.startswith("image/"):
            upload_text = "Image uploaded."

        st.session_state.uploaded_content = upload_text
        st.success("File uploaded.")

    prompt = st.text_input("Ask your question:")
    if prompt:
        full_prompt = prompt
        if st.session_state.uploaded_content:
            full_prompt += f"\n\nDocument Content:\n{st.session_state.uploaded_content}"

        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert in building emissions and sustainable materials."},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"API Error: {e}"
            st.session_state.chat_history.append((prompt, reply))

    for i, (q, a) in enumerate(st.session_state.chat_history):
        message(q, is_user=True, key=f"user_{i}")
        message(a, key=f"bot_{i}")
