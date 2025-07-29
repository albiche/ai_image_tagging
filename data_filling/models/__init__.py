# data_filling/models/__init__.py

from .vision_gpt import VisionGPTModel

def get_model(conf):
    if conf["model"] == "vision_gpt":
        return VisionGPTModel(conf)
    else:
        raise ValueError(f"Modèle inconnu : {conf['model']}")
