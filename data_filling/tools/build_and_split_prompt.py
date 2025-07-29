# data_filling/tools/build_and_split_prompt.py

from typing import List, Dict, Tuple, Optional
import json
import tiktoken
import random

def estimate_tokens_from_messages(messages: List[Dict], model: str = "gpt-4o") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    total = 0
    for m in messages:
        content = m.get("content")
        if isinstance(content, str):
            total += len(enc.encode(content))
        elif isinstance(content, list):
            for part in content:
                if part["type"] == "text":
                    total += len(enc.encode(part["text"]))
                elif part["type"] == "image_url":
                    total += 100  # estimation OpenAI pour 1 image
    return total


def build_prompt_messages(fields_dict: Dict, images_b64: List[str], ocr_context: str | None = None) -> List[Dict]:
    """Assemble un message complet format OpenAI avec un sous-ensemble de champs + images."""
    fields = {
        k: {
            "description": v["prompt_ai"],
            "accepted_values": v.get("accepted_values", [])
        }
        for k, v in fields_dict.items()
    }

    system_prompt = (
        "You are an expert in marketing analysis for alcoholic beverage products.\n"
        "You are given one product image. Your task is to extract structured information from the image.\n"
        "Return a valid JSON dictionary with key: value pairs.\n"
        "Use only the keys and descriptions provided below. If you have no clue, return 'N/A'.\n"
        "Respond in the format: {key: value, ...} with no explanation.\n\n"
        f"Fields:\n{json.dumps(fields)}"
    )

    user_content = [{"type": "text", "text": "Here are the product images:"}]
    if ocr_context:
        user_content.append({"type": "text", "text": f"Context OCR:\n{ocr_context}"})
    user_content += [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        for b64 in images_b64
    ]


    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]



def smart_split_prompt(
    prompt_data: Dict,
    images_b64: List[str],
    ocr_context: str | None = None,
    max_tokens: int = 8000,
    model: str = "gpt-4o",
    max_images_per_chunk: int = 3,
    max_chunks: int = 10,
    max_fields_per_chunk: Optional[int] = None
) -> List[Tuple[Dict, List[str], Optional[str]]]:
    """
    Split intelligently the fields in chunks to respect token and image constraints.

    Args:
        prompt_data: dict of fields (tags) to include
        images_b64: list of base64-encoded images
        max_tokens: max token count per prompt
        model: model used for token estimation
        max_images_per_chunk: max number of images allowed (random sample if exceeded)
        max_chunks: max number of allowed chunks total
        max_fields_per_chunk: optional max number of fields per chunk (None = no limit)

    Returns:
        List of (fields_chunk, image_chunk) or [] if aborted
    """
    all_chunks = []

    # Échantillonner les images si on dépasse la limite
    if len(images_b64) > max_images_per_chunk:
        image_chunk = random.sample(images_b64, max_images_per_chunk)
    else:
        image_chunk = images_b64

    field_keys = list(prompt_data.keys())
    i = 0

    while i < len(field_keys):
        current_fields = {}
        field_count = 0

        while i < len(field_keys) and (max_fields_per_chunk is None or field_count < max_fields_per_chunk):
            key = field_keys[i]
            val = prompt_data[key]
            test_fields = {**current_fields, key: val}

            token_estimate = estimate_tokens_from_messages(
                build_prompt_messages(test_fields, image_chunk, ocr_context),
                model
            )

            if token_estimate > max_tokens:
                if not current_fields:
                    print(f"⚠️ Field '{key}' is too heavy on its own. Forcing as single-field chunk.")
                    all_chunks.append(({key: val}, image_chunk))
                    i += 1
                else:
                    break  # stop adding more fields, save current chunk
            else:
                current_fields[key] = val
                field_count += 1
                i += 1

        if current_fields:
            all_chunks.append((current_fields.copy(), image_chunk))

    if len(all_chunks) > max_chunks:
        print(f"❌ Skipping prompt: {len(all_chunks)} chunks needed (max allowed is {max_chunks}).")
        return []

    return all_chunks


def merge_responses(responses: List[Dict]) -> Dict:
    final = {}
    for r in responses:
        final.update(r)
    return final