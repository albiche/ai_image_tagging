# data_filling/tools/extract_text.py

from typing import List, Dict, Tuple, Optional


from typing import List, Dict

def build_extract_text_messages(images_b64: List[str]) -> List[Dict]:
    """
    Vision prompt STRICT : GPT doit simplement renvoyer le texte visible.
    """
    system_prompt = (
        "You are a high-precision OCR assistant.\n"
        "Read **only** the legible text on the images.\n"
        "• Do NOT identify the product, brand, object or scene.\n"
        "• Do NOT add explanations or formatting.\n"
        "If no text is visible, answer exactly: N/A"
    )

    user_content = (
        [{"type": "text", "text": "Please transcribe all text:"}] +
        [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"},
            }
            for b64 in images_b64[:1]   # 1 seule image pour l'OCR
        ]
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_content},
    ]
