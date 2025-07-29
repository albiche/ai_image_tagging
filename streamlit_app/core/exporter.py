# streamlit_app/core/exporter.py

import json
import os

def save_schema_json(schema: dict, name: str):
    path = f"data/schemas/{name}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(schema, f, indent=2)
