import streamlit as st
import pandas as pd
from io import BytesIO
from streamlit_chat import message
from openai import OpenAI
import os
import pdfplumber
from PIL import Image

st.set_page_config(page_title="BEAM - Emissions App", layout="wide", page_icon="♻️")

# Header with logo
st.markdown(
    "<div style='display: flex; align-items: center; justify-content: space-between;'>"
    "<img src='https://neotericremodelling.ca/wp-content/uploads/2024/01/cropped-NEOTERIC_Logo_Black-Transparent-300x79.png' width='180'/>"
    "<h1 style='text-align: right; color: #3f51b5;'>♻️ BEAM - Building Emissions Accounting Model</h1>"
    "</div><hr>",
    unsafe_allow_html=True
)

# Emoji-based sidebar navigation
with st.sidebar:
    page = st.radio("Navigation", [
        "🏗️ Project Info",
        "🧱 Components",
        "📊 Results",
        "🤖 AI Assistant"
    ])

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY"))

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

if "uploaded_content" not in st.session_state:
    st.session_state.uploaded_content = ""

# Pages
if page == "🏗️ Project Info":
    st.markdown("## 🏗️ Project Information")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name", "Example Project")
            building_type = st.selectbox("Building Type", ["Office", "Residential", "School", "Hospital"])
        with col2:
            floor_area = st.number_input("Floor Area (m²)", min_value=0, value=5000)
            project_id = st.text_input("Project ID", "AUTO123")
        if st.button("💾 Save Project Info"):
            st.success("✅ Project information saved successfully.")

elif page == "🧱 Components":
    st.markdown("## 🧱 Component Materials")
    selected_component = st.selectbox("Select Component", components)
    edited_df = st.data_editor(
        st.session_state.component_data[selected_component],
        num_rows="dynamic",
        use_container_width=True
    )
    edited_df["Emissions (kg CO2e)"] = edited_df["Quantity"] * edited_df["Emission Factor (kg CO2e/unit)"]
    st.session_state.component_data[selected_component] = edited_df

    if st.button("🔁 Recalculate Emissions"):
        total = edited_df["Emissions (kg CO2e)"].sum()
        st.success(f"✅ Emissions for {selected_component}: {total / 1000:.2f} t CO₂e")

elif page == "📊 Results":
    st.markdown("## 📊 Emissions Summary")
    all_data = pd.concat(st.session_state.component_data.values(), ignore_index=True)
    summary_df = all_data.groupby("Material")[["Emissions (kg CO2e)"]].sum().reset_index()
    summary_df["Emissions (t CO2e)"] = summary_df["Emissions (kg CO2e)"] / 1000
    total = summary_df["Emissions (t CO2e)"].sum()
    st.metric("🌍 Total Emissions", f"{total:.1f} t CO2e")
    st.dataframe(summary_df[["Material", "Emissions (t CO2e)"]], use_container_width=True)
    st.bar_chart(summary_df.set_index("Material")["Emissions (t CO2e)"])

    st.markdown("### 📥 Export Results")
    if st.button("⬇️ Download Excel Report"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for name, df in st.session_state.component_data.items():
                df.to_excel(writer, sheet_name=name[:31], index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
        output.seek(0)
        st.download_button("📄 Download Excel", output, file_name="beam_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif page == "🤖 AI Assistant":
    st.markdown("## 🤖 BEAM Assistant")
    st.markdown("You can also upload a design file for analysis (PDF or image).")
    uploaded_file = st.file_uploader("Upload your building design file", type=["pdf", "png", "jpg"])
    upload_text = "Uploaded image received. (Optical analysis not included here.)""

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                pages = [page.extract_text() for page in pdf.pages]
                upload_text = "Uploaded image received. (Optical analysis not included here.)"
".join(filter(None, pages))
        elif uploaded_file.type.startswith("image/"):
            image = Image.open(uploaded_file)
            upload_text = "Uploaded image received. (Optical analysis not included here.)"Uploaded image received. (Optical analysis not included here.)"

        st.session_state.uploaded_content = upload_text
        st.success("✅ File uploaded successfully.")

    prompt = st.text_input("Ask BEAM Assistant:")

    if prompt:
        full_prompt = prompt
        if st.session_state.uploaded_content:
            full_prompt += f"

Also consider the following document content:
{st.session_state.uploaded_content}"

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

    for i, (user, bot) in enumerate(st.session_state.chat_history):
        message(user, is_user=True, key=f"user_{i}")
        message(bot, key=f"bot_{i}")