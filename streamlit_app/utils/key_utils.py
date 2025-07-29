# streamlit_app/utils/key_utils.py

import re
import os

def generate_default_key(label: str) -> str:
    return re.sub(r'\W+', '_', label.strip().lower()).strip('_')

def is_key_unique(proposed_key: str, current_col: str, global_keys: dict) -> bool:
    return all(col == current_col or key != proposed_key for col, key in global_keys.items())
