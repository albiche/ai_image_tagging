# data_filling/agents/base_agent.py

import base64, json, cv2, httpx, numpy as np
from openai import OpenAI


class BaseGPTAgent:
    """Fonctions communes (client, _chat, encodage, parse)."""

    # ------------------------------------------------------------------ #
    #  Construction
    # ------------------------------------------------------------------ #
    def __init__(self, config: dict):
        self._config      = config
        self._model_name  = config.get("openai_model", "gpt-4o")
        self._client: OpenAI = self._build_client()

    def _build_client(self) -> OpenAI:
        api_key = self._config.get("openai_api_key")
        if not api_key:
            raise ValueError("Missing 'openai_api_key' in config.")
        if not self._config.get("verify_ssl", True):
            print("⚠️ SSL verification disabled for OpenAI client (dev mode).")
            return OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))
        return OpenAI(api_key=api_key)

    # ------------------------------------------------------------------ #
    #  Chat helper (robuste)
    # ------------------------------------------------------------------ #
    def _completion_param(self, n_tokens: int) -> dict:
        return (
            {"max_completion_tokens": n_tokens}
            if self._model_name.lower().startswith("o")
            else {"max_tokens": n_tokens}
        )

    def _chat(self, *, messages, n_tokens=4096, temperature: float = 0.0, **extra):
        """
        Envoie la requête chat. Essaye successivement :
        1. full params (temperature + n_tokens + extra)
        2. sans temperature
        3. sans extra ni temperature
        4. seulement model/messages
        """
        base = dict(model=self._model_name, messages=messages)
        trials = [
            {**self._completion_param(n_tokens), "temperature": temperature, **extra},
            {**self._completion_param(n_tokens), **extra},
            self._completion_param(n_tokens),
            {},
        ]

        last_err = None
        for params in trials:
            try:
                return self._client.chat.completions.create(**base, **params)
            except Exception as e:
                last_err = e
                # on itère si l'erreur mentionne « unsupported parameter »
                if "unsupported parameter" not in str(e).lower():
                    break
        raise last_err

    # ------------------------------------------------------------------ #
    #  Parsing JSON de la réponse
    # ------------------------------------------------------------------ #
    @staticmethod
    def parse_json_response(content: str) -> dict:
        """
        Essaie d’extraire le premier objet JSON trouvé. Renvoie {} si échec.
        """
        txt = content.strip()
        if txt.startswith("```json"):
            txt = txt[7:].strip()
        if txt.endswith("```"):
            txt = txt[:-3].strip()
        l, r = txt.find("{"), txt.rfind("}") + 1
        if l >= 0 and r > l:
            try:
                return json.loads(txt[l:r])
            except Exception as e:
                print(f"⚠️ JSON parsing error: {e}")
        return {}

    # ------------------------------------------------------------------ #
    #  Utilitaire images → base64
    # ------------------------------------------------------------------ #
    @staticmethod
    def encode_bgr_to_b64(frame: np.ndarray) -> str:
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            raise ValueError("Failed to encode frame.")
        return base64.b64encode(buf).decode()
