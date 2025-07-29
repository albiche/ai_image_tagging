# streamlit_app/ui/column_editor.py

import streamlit as st
import pandas as pd
from streamlit_app.core.format_guesser import guess_free_format
from streamlit_app.utils.key_utils import generate_default_key

def _add_value_to_multiselect(col_name: str):
    input_key = f"newval_temp_{col_name}"
    multi_key = f"multi_{col_name}"
    new_val = st.session_state.get(input_key, "").strip()
    if new_val and new_val not in st.session_state.get(multi_key, []):
        st.session_state[multi_key].append(new_val)
    st.session_state[input_key] = ""

def edit_column_schema(col_name: str, detected: dict, col_values: pd.Series) -> dict:
    result = {"accepted_values": None, "prompt_ai": None, "key": None}

    # 1. Mode radio
    mode_key = f"mode_{col_name}"
    mode = st.radio(f"Mode for `{col_name}`", ["categorial", "free"],
                    index=0 if detected["mode"] == "categorial" else 1,
                    horizontal=True,
                    key=mode_key)

    # 2. Mode CATEGORIAL
    if mode == "categorial":
        multi_key = f"multi_{col_name}"
        display_key = f"display_{col_name}"
        input_key = f"newval_temp_{col_name}"

        if multi_key not in st.session_state:
            raw_vals = detected.get("accepted_values", [])
            initial_vals = []

            if isinstance(raw_vals, list) and all(len(v) == 1 for v in raw_vals) and len(raw_vals) > 3:
                initial_vals = []  # probable mauvaise détection ['S', 'T', 'R']
            elif isinstance(raw_vals, list):
                initial_vals = raw_vals.copy()

            if initial_vals == ["Yes"]:
                initial_vals.append("No")
            elif initial_vals == ["No"]:
                initial_vals.append("Yes")

            st.session_state[multi_key] = initial_vals

        st.text_input(f"➕ Add value", key=input_key,
                      on_change=_add_value_to_multiselect, args=(col_name,))

        current_vals = list(dict.fromkeys(st.session_state.get(multi_key, [])))
        selected = st.multiselect("✅ Current accepted values", options=current_vals,
                                  default=current_vals, key=display_key)

        st.session_state[multi_key] = selected
        result["accepted_values"] = selected

        if not selected:
            st.warning("⚠️ No accepted values defined.")

    # 3. Mode FREE
    else:
        non_null = col_values.dropna().astype(str).unique().tolist()
        auto_example = non_null[0] if non_null else "No data"
        auto_format = guess_free_format(auto_example)

        format_key = f"format_{col_name}"
        example_key = f"example_select_{col_name}"

        format_val = st.text_input("🧾 Format", value=auto_format, key=format_key)
        example_val = st.selectbox("🎯 Example", options=non_null or ["No data"], index=0, key=example_key)

        result["accepted_values"] = f"{format_val} (e.g., {example_val})"

    # 4. Prompt
    prompt_key = f"prompt_ai_{col_name}"
    default_prompt = st.session_state.get(prompt_key, col_name)

    prompt_val = st.text_area("🤖 Prompt for AI", value=default_prompt, key=prompt_key)


    result["prompt_ai"] = prompt_val

    # 5. Clé
    key_key = f"key_{col_name}"
    default_key = generate_default_key(col_name)

    if key_key not in st.session_state:
        st.session_state[key_key] = default_key

    key_val = st.text_input("🔑 Unique key", value=st.session_state[key_key], key=key_key)
    result["key"] = key_val

    # 6. HARD RESET
    with st.expander("⚙️ Advanced"):
        if st.button(f"🔄 Reset ALL for `{col_name}`", key=f"reset_full_{col_name}"):
            for suffix in [
                f"mode_{col_name}", f"multi_{col_name}", f"display_{col_name}",
                f"format_{col_name}", f"example_select_{col_name}",
                f"prompt_ai_input_{col_name}", f"prompt_ai_{col_name}",
                f"key_{col_name}", f"newval_temp_{col_name}"
            ]:
                st.session_state.pop(suffix, None)
            st.rerun()

    return result
