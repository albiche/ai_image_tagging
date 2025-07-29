# data_filling/pipelines/run_from_folder.py

import os
import pandas as pd

from data_filling.models import get_model
from data_filling.tools.post_rules import apply_logic_rules
from .tool_pipeline import gather_media_files, optimize_image


def run_pipeline_folder(conf: dict):
    """
    Pipeline pour traiter un dossier structuré par row_id avec des fichiers média.
    """
    model            = get_model(conf)
    root_dir         = conf["data_path"]
    out_csv          = conf["output_path"]
    convert_png      = conf.get("convert_png", False)
    use_optimize     = conf.get("optimize_image", False)
    save_as_jpeg     = conf.get("save_as_jpeg", True)

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    preds, tmp_files = [], []

    for row_id in sorted(os.listdir(root_dir)):
        row_dir = os.path.join(root_dir, row_id)
        if not os.path.isdir(row_dir):
            continue

        media, temps = gather_media_files(row_dir, convert_png=convert_png)
        tmp_files.extend(temps)

        if not media:
            print(f"⚠️ No media in {row_id}")
            continue

        optimized_media = []
        for path in media:
            if use_optimize:
                try:
                    opt_path = optimize_image(
                        path,
                        save_as_jpeg=save_as_jpeg
                    )
                    tmp_files.append(opt_path)
                    optimized_media.append(opt_path)
                except Exception as e:
                    print(f"⚠️ Optimize error « {os.path.basename(path)} »: {e}")
            else:
                optimized_media.append(path)

        print(f"🔍 {row_id} ({len(optimized_media)} files)")
        try:
            pred = model.predict(optimized_media)
            pred["row_id"] = row_id
            preds.append(pred)
        except Exception as e:
            print(f"❌ {row_id}: {e}")

    if preds:
        df = pd.DataFrame(preds).set_index("row_id")
        if conf.get("logic_rules_path"):
            df = apply_logic_rules(df, conf["logic_rules_path"])
        df.to_csv(out_csv, sep=",", encoding="utf-8-sig")
        print(f"✅ saved → {out_csv}")
    else:
        print("⚠️ No predictions generated.")

    for f in tmp_files:
        try: os.remove(f)
        except: pass
