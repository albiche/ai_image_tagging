# data_filling/agents/text_extraction_agent.py

from __future__ import annotations
from typing import List

from .base_agent import BaseGPTAgent
from data_filling.tools.extract_text import build_extract_text_messages


class TextExtractionAgent(BaseGPTAgent):
    """
    OCR par GPT : renvoie **tout** le texte détecté dans les images.

    Utilise le helper _chat() du BaseGPTAgent, donc fonctionne
    indifféremment avec les modèles o-series (« o1 », « o3 », …)
    ou GPT-4 / GPT-4o / GPT-3.5-turbo.
    """

    def extract(self, images_b64: List[str]) -> str:
        messages = build_extract_text_messages(images_b64)


        # _chat() gère automatiquement max_tokens vs max_completion_tokens
        # et retire temperature si le modèle ne l’accepte pas.
        # et retire temperature si le modèle ne l’accepte pas.
        resp = self._chat(messages=messages, n_tokens=10000, temperature=0)

        return resp.choices[0].message.content.strip()
