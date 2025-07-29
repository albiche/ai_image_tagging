# streamlit_app/core/format_guesser.py

import re

def guess_free_format(example: str) -> str:
    ex = example.strip()

    if re.search(r"[£€$]", ex):
        return "PRICE"
    if re.search(r"\d+(\.\d+)?\s*(mL|cl|L)", ex, re.IGNORECASE):
        return "VOLUME"
    if "%" in ex:
        return "PERCENT"
    if re.fullmatch(r"[+-]?\d+\.\d+", ex):
        return "FLOAT"
    if re.fullmatch(r"[+-]?\d+", ex):
        return "INT"
    return "STRING"
