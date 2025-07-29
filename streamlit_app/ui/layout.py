# streamlit_app/ui/layout.py

import streamlit as st
import pandas as pd
from streamlit_app.core.schema_detector import detect_accepted_values
from streamlit_app.ui.column_editor import edit_column_schema

def run_ui():
    uploaded_file = st.file_uploader("📁 Upload a CSV file", type=["csv"])
    if not uploaded_file:
        return None, None

    df = pd.read_csv(uploaded_file)
    all_cols = df.columns.tolist()

    if "selection_mode" not in st.session_state:
        st.session_state.selection_mode = "select_all"
    if "active_cols" not in st.session_state:
        st.session_state.active_cols = all_cols.copy()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Select All"):
            st.session_state.selection_mode = "select_all"
            st.session_state.active_cols = all_cols.copy()
    with col2:
        if st.button("❌ Deselect All"):
            st.session_state.selection_mode = "deselect_all"
            st.session_state.active_cols = []

    if st.session_state.selection_mode == "select_all":
        excluded = st.multiselect("🗑️ Exclude columns", all_cols)
        selected_cols = [c for c in all_cols if c not in excluded]
    else:
        included = st.multiselect("➕ Include columns", all_cols)
        selected_cols = included

    st.session_state.active_cols = selected_cols

    st.subheader("📊 Data Preview")
    if selected_cols:
        st.dataframe(df[selected_cols].head(5), use_container_width=True)

    st.subheader("🛠️ Edit Accepted Values")
    initial_schema = detect_accepted_values(df[selected_cols])
    updated_schema = {}
    used_keys = {}

    has_duplicates = False
    # 🧼 Cleanup session state for deselected columns
    for col in all_cols:
        if col not in selected_cols:
            for suffix in [
                "multi_", "newval_temp_", "display_", "format_",
                "example_select_", "prompt_ai_", "key_", "mode_"
            ]:
                key = f"{suffix}{col}"
                if key in st.session_state:
                    del st.session_state[key]

    for col in selected_cols:
        st.markdown(f"---\n#### 🔧 `{col}`")
        result = edit_column_schema(col, initial_schema[col], df[col])

        proposed_key = result.get("key")
        if proposed_key in used_keys.values():
            st.error(f"❌ Duplicate key: `{proposed_key}` already used.")
            has_duplicates = True

        used_keys[col] = proposed_key
        updated_schema[col] = result

    if has_duplicates:
        st.warning("🚫 Please fix all duplicate keys before exporting.")
        return None, None

    file_name = st.text_input("📁 Output file name (without .json)", value="fields_schema").strip()
    return updated_schema, file_name
