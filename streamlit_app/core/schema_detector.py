# streamlit_app/core/schema_detector.py

import re
import pandas as pd

def detect_column_type_and_format(values: pd.Series) -> dict:
    non_null = values.dropna().astype(str).str.strip()
    uniques = non_null.unique().tolist()
    total_count = len(non_null)
    unique_count = len(uniques)

    if total_count == 0:
        return {
            "mode": "free",
            "accepted_values": "STRING"
        }

    # Paramètres de seuils
    MIN_DIGIT_RATIO = 0.8         # au moins 80% des valeurs contiennent un chiffre
    MAX_CATEGORIAL_UNIQUES = 40   # au-delà => on passe en free
    MAX_UNIQUE_RATIO = 0.5        # si > 50% de taux d'unicité => free

    digit_count = sum(bool(re.search(r"\d", val)) for val in non_null)
    digit_ratio = digit_count / total_count
    unique_ratio = unique_count / total_count

    if (
        digit_ratio >= MIN_DIGIT_RATIO or
        unique_count > MAX_CATEGORIAL_UNIQUES or
        unique_ratio > MAX_UNIQUE_RATIO
    ):
        return {
            "mode": "free",
            "accepted_values": "STRING",
            "example": uniques[0]
        }

    # Sinon : catégorial
    return {
        "mode": "categorial",
        "accepted_values": sorted(uniques)
    }


def detect_accepted_values(df: pd.DataFrame) -> dict:
    return {
        col: detect_column_type_and_format(df[col])
        for col in df.columns
    }
