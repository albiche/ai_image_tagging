# data_filling/agents/split_vision_agent.py

from __future__ import annotations
from typing import Dict, List, Tuple

from .base_agent import BaseGPTAgent
from data_filling.tools.build_and_split_prompt import (
    smart_split_prompt,
    build_prompt_messages,
)


class SplitVisionAgent(BaseGPTAgent):
    """Découpe les champs, interroge GPT, valide les réponses."""

    # ------------------------------------------------------------------ #
    #  Interface publique
    # ------------------------------------------------------------------ #
    def predict_fields(
            self,
            prompt_dict: Dict,
            images_b64: List[str],
            *,
            ocr_context: str | None = None,
            extra_context: str | None = None,  # 🆕
            double_check: bool = False,
            max_fields_per_chunk: int | None = None,
    ) -> Dict:
        first_pass = self._run_and_retry(
            prompt_dict, images_b64, max_fields_per_chunk, ocr_context, extra_context
        )

        if not double_check:
            return self._fill_na(prompt_dict, first_pass)

        second_pass = self._run_and_retry(prompt_dict, images_b64, max_fields_per_chunk, ocr_context, extra_context)
        agreed, conflicts = self._compare(first_pass, second_pass, prompt_dict)

        if conflicts:
            final_retry = self._run_and_retry(conflicts, images_b64, max_fields_per_chunk, ocr_context, extra_context)
            agreed.update(final_retry)

        return self._fill_na(prompt_dict, agreed)

    # ------------------------------------------------------------------ #
    #  Implémentation privée
    # ------------------------------------------------------------------ #
    def _run_and_retry(
            self,
            fields: Dict,
            images_b64: List[str],
            max_fields_per_chunk: int | None,
            ocr_context: str | None = None,
            extra_context: str | None = None,  # 🆕
    ) -> Dict:
        validated, invalids = self._ask_chunks(fields, images_b64, max_fields_per_chunk, ocr_context, extra_context)
        print("fields", fields, "\n")
        print("ocr_context",ocr_context,"\n")
        print("validated ", validated, "\ninvalids ", invalids, "\n\n")

        if not invalids:
            return validated

        # ✅ reconstruction correcte du prompt d'origine
        invalids_prompt = {
            k: fields[k]
            for k in invalids
            if k in fields
        }

        retry_valid, _ = self._ask_chunks(
            invalids_prompt, images_b64, max_fields_per_chunk, ocr_context, extra_context, retry=True
        )

        print("retry_valid", retry_valid)
        validated.update(retry_valid)
        return validated

    # ---------- découpe + GPT -----------------------------------------
    def _ask_chunks(
            self,
            prompt_data: Dict,
            images_b64: List[str],
            max_fields_per_chunk: int | None,
            ocr_context: str | None = None,
            extra_context: str | None = None,  # 🆕
            *,
            retry: bool = False,
    ) -> Tuple[Dict, Dict]:
        chunks = smart_split_prompt(
            prompt_data,
            images_b64,
            ocr_context=ocr_context,
            extra_context=extra_context,  # 🆕
            model=self._model_name,
            max_fields_per_chunk=max_fields_per_chunk,
            max_images_per_chunk=6,
            max_tokens=10_000,
            max_chunks=15 if not retry else 10,
        )
        if not chunks:
            return {k: "N/A" for k in prompt_data}, {}

        raw: Dict = {}
        for i, (field_chunk, img_chunk) in enumerate(chunks, 1):
            print(f"🧩 GPT {'Retry ' if retry else ''}{i}/{len(chunks)} — {len(field_chunk)} fields")
            resp = self._call_gpt(field_chunk, img_chunk, ocr_context, extra_context)
            raw.update(resp)

        return self._validate_resp(raw, prompt_data)

    # ---------- appel GPT unique --------------------------------------
    def _call_gpt(self, fields, images_b64, ocr_context, extra_context):
        messages = build_prompt_messages(fields, images_b64, ocr_context=ocr_context, extra_context=extra_context)

        try:
            response = self._chat(
                messages=messages,
                n_tokens=10_000,
                response_format={"type": "json_object"},
            )
        except Exception as err:
            print("⚠️ first _chat() failed →", err)
            response = self._chat(messages=messages, n_tokens=4_000)

        raw_txt = response.choices[0].message.content


        data = self.parse_json_response(raw_txt)

        if not data:  # vide ou mal parsé
            raise ValueError("GPT returned no valid JSON")

        return data

    # ---------- validation & helpers ----------------------------------
    def _validate_resp(self, raw: Dict, ref_prompt: Dict) -> Tuple[Dict, Dict]:
        valid, invalid = {}, {}
        for k, v in raw.items():
            if k not in ref_prompt:
                continue

            val = str(v).strip()
            accepted = ref_prompt[k].get("accepted_values", [])

            if val == "N/A":
                valid[k] = "N/A"

            # --- ① accepted = LISTE non vide  → contrôle strict
            elif isinstance(accepted, list) and accepted:
                if val in accepted:
                    valid[k] = val
                else:
                    invalid[k] = val  # ira au retry

            # --- ② accepted = chaîne ou liste vide → texte libre
            else:
                valid[k] = val

        return valid, invalid

    @staticmethod
    def _compare(v1: Dict, v2: Dict, ref: Dict) -> Tuple[Dict, Dict]:
        agreed, conflicts = {}, {}
        for k in ref:
            if v1.get(k) == v2.get(k):
                agreed[k] = v1.get(k, "N/A")
            else:
                conflicts[k] = ref[k]
        return agreed, conflicts

    @staticmethod
    def _fill_na(ref: Dict, partial: Dict) -> Dict:
        filled = partial.copy()
        for k in ref:
            filled.setdefault(k, "N/A")
        return filled
