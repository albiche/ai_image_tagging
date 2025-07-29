# streamlit_app/app.py
import streamlit as st
from streamlit_app.ui.layout import run_ui
from streamlit_app.core.exporter import save_schema_json

st.set_page_config(page_title="Schema Editor", layout="wide")
st.title("🧠 Accepted Values Schema Builder")

schema, file_name = run_ui()

if schema:
    st.subheader("✅ Schema Preview")
    st.json(schema, expanded=False)

    if st.button("📂 Export as JSON"):
        save_schema_json(schema, file_name)
        st.success(f"Schema saved to data_filling/ressources/{file_name}.json")
