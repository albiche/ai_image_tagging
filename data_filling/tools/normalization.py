# data_filling/tools/normalization.py

from copy import deepcopy

def normalize_output(gpt_response: dict, template: dict) -> dict:
    """
    Complete the GPT response based on the template.
    Missing fields are filled with 'N/A'.
    """
    response = deepcopy(template)
    for k in response:
        if k in gpt_response:
            response[k] = gpt_response[k]
    return response

