# data_filling/models/vision_gpt.py

import copy
from typing import List

import numpy as np
from data_filling.data.io import get_images_from_case
from data_filling.tools.template import (
    load_template,
    transform_template_for_prompt,
    revert_prompt_response,
)
from data_filling.tools.normalization import normalize_output
from data_filling.agents import SplitVisionAgent, TextExtractionAgent


class VisionGPTModel:
    """
    Prépare les données, appelle les agents et renvoie un dictionnaire
    normalisé.  Robuste : aucune mutation du template maître, gestion
    d’erreurs sur revert / OCR facultatif.
    """

    # ------------------------------------------------------------------ #
    #  Construction
    # ------------------------------------------------------------------ #
    def __init__(self, conf: dict):
        self.conf = conf

        # template maître (immuable)
        self._template = load_template(conf["template_path"])
        self._prompt_tpl_clean = transform_template_for_prompt(self._template)

        # Agents
        self._split_agent = SplitVisionAgent(conf)
        self._ocr_agent   = TextExtractionAgent(conf)

    # ------------------------------------------------------------------ #
    #  Helpers internes
    # ------------------------------------------------------------------ #
    def _images_to_b64(self, media_paths: List[str]) -> List[str]:
        frames = get_images_from_case(
            media_paths,
            mode=self.conf.get("video_frame_strategy", "dynamic"),
        )
        if not frames:
            raise ValueError("No frames found.")
        return [self._split_agent.encode_bgr_to_b64(f) for f in frames]

    def _prepare_prompt_dict(self) -> tuple[dict, dict]:
        """
        Copie défensive du template ; sépare champs avec prompt_ai
        et ceux à remplir par N/A.
        """
        wanted, na = {}, {}
        for k, meta in copy.deepcopy(self._prompt_tpl_clean).items():
            if {"prompt_ai", "accepted_values"} <= meta.keys():
                wanted[k] = meta
            else:
                na[k] = "N/A"
        return wanted, na

    # ------------------------------------------------------------------ #
    #  API publique
    # ------------------------------------------------------------------ #
    def predict(self, media_paths: List[str], context: str | None = None) -> dict:
        imgs_b64 = self._images_to_b64(media_paths)

        wanted, na_fields = self._prepare_prompt_dict()

        ocr_ctx = None
        if self.conf.get("add_transcription", False):
            ocr_ctx = self._ocr_agent.extract(imgs_b64) or None

        validated = self._split_agent.predict_fields(
            wanted,
            imgs_b64,
            ocr_context=ocr_ctx,
            extra_context=context,  # 🆕 Ajout du paramètre
            double_check=self.conf.get("double_check", False),
            max_fields_per_chunk=self.conf.get("max_fields_per_chunk"),
        )

        validated.update(na_fields)

        # ---------- revert + normalisation protégés -----------------
        try:
            final = revert_prompt_response(validated, self._template)
            final = normalize_output(final, self._template)
            if not isinstance(final, dict):
                raise TypeError("Final result is not a dict")
        except Exception as e:
            print("⚠️ post-processing failed:", e)
            print("   validated keys →", list(validated)[:10])
            final = validated

        return final

