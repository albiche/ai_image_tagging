# data_filling/tools/export.py

import pandas as pd
from data_filling.tools.normalization import normalize_output

def outputs_to_dataframe(output_list: list[tuple[str, dict]], template: dict) -> pd.DataFrame:
    """
    Convert a list of (row_id, gpt_output_dict) into a complete DataFrame.
    """
    normalized_rows = []
    row_ids = []

    for row_id, raw in output_list:
        normalized = normalize_output(raw, template)
        normalized_rows.append(normalized)
        row_ids.append(row_id)

    df = pd.DataFrame(normalized_rows, index=row_ids)
    df.index.name = "row_id"
    return df

def save_dataframe(df: pd.DataFrame, path: str, sep: str = "\t"):
    df.to_csv(path, sep=sep, index=True)
    print(f"✅ File saved at: {path}")
