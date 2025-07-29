# data_filling/tools/template.py

import json
import re
import unicodedata


def load_template(template_path="data_filling/resources/template_fields.json"):
    """Load the standard template with all fields initialized to 'N/A'."""
    with open(template_path, "r") as f:
        return json.load(f)

def transform_template_for_prompt(template: dict) -> dict:
    """
    Transform the raw template into {normalized_key: {...}}.
    Only includes 'prompt_ai' and 'accepted_values' if they exist in the input.
    """
    prompt_template = {}

    for original_field, props in template.items():
        normalized_key = props.get("key")
        if not normalized_key:
            raise ValueError(f"Missing 'key' (normalized_key) for field: {original_field}")

        result = {}

        if "prompt_ai" in props:
            result["prompt_ai"] = props["prompt_ai"]
        if "accepted_values" in props:
            result["accepted_values"] = props["accepted_values"]

        prompt_template[normalized_key] = result

    return prompt_template


def revert_prompt_response(gpt_response: dict, original_template: dict) -> dict:
    """
    Maps normalized_key (e.g. 'brand_pr_vs_comp') back to original column name.
    """
    key_to_column = {
        props["key"]: column_name
        for column_name, props in original_template.items()
        if "key" in props
    }

    reverted = {}
    for norm_key, value in gpt_response.items():
        original_column = key_to_column.get(norm_key)
        if original_column:
            reverted[original_column] = value
        else:
            print(f"⚠️ Unknown key in GPT response: {norm_key}")
    return reverted


