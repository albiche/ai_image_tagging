# data_filling/pipelines/run_from_csv.py

import os
import pandas as pd
from data_filling.models import get_model
from data_filling.tools.post_rules import apply_logic_rules
from .tool_pipeline import download_image_tmp, convert_png_to_jpg, optimize_image


def run_pipeline_csv(conf: dict):
    # 📌 Charge modèle
    model = get_model(conf)

    # 📌 Config de base
    csv_path = conf["dataset_link"]["path"]
    url_column = conf["dataset_link"]["column"]
    out_csv = conf["output_path"]
    nb_max = conf.get("nb_max")
    convert_png = conf.get("convert_png", False)
    use_optimize = conf.get("optimize_image", False)
    save_as_jpeg = conf.get("save_as_jpeg", True)
    link_column_name = conf.get("link_column_name", "Link to Asset")

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    # 📌 Charge CSV source
    df = pd.read_csv(csv_path)
    if nb_max:
        df = df.head(nb_max)

    preds = []
    tmp_files = []

    for idx, row in df.iterrows():
        url = row[url_column]
        print(f"\n========== ROW {idx} ==========")

        # 1️⃣ Téléchargement
        try:
            img_path = download_image_tmp(url)
            tmp_files.append(img_path)
            print("✓ Downloaded", img_path)
        except Exception as e:
            print(f"❌ download error: {e}")
            continue

        # 2️⃣ Conversion PNG → JPG
        if convert_png and img_path.lower().endswith(".png"):
            try:
                img_path = convert_png_to_jpg(img_path)
                tmp_files.append(img_path)
                print("✓ PNG converted →", img_path)
            except Exception as e:
                print(f"⚠️ convert error: {e}")

        # 3️⃣ Optimisation
        if use_optimize:
            try:
                img_path = optimize_image(img_path, save_as_jpeg=save_as_jpeg)
                tmp_files.append(img_path)
                print("✓ Optimized →", img_path)
            except Exception as e:
                print(f"⚠️ optimize error: {e}")

        # 4️⃣ Prédiction
        try:
            pred = model.predict([img_path])
            if not isinstance(pred, dict):
                raise ValueError("model.predict returned non-dict")

            # ✅ Ajoute le lien complet en premier
            pred = {link_column_name: url, **pred}

            preds.append(pred)
            print("✓ Prediction OK")
        except Exception as e:
            print(f"❌ predict error: {e}")

    # 5️⃣ Sortie CSV
    if preds:
        df_pred = pd.DataFrame(preds)

        # 🔎 Post-rules éventuelles
        if conf.get("logic_rules_path"):
            df_pred = apply_logic_rules(df_pred, conf["logic_rules_path"])

        # 🔎 Colonnes dans l'ordre voulu (optionnel)
        ordered_columns = None
        if conf.get("column_order"):
            ordered_columns = conf["column_order"]
        elif conf.get("column_order_path"):
            with open(conf["column_order_path"]) as f:
                ordered_columns = [line.strip() for line in f if line.strip()]

        if ordered_columns:
            for col in ordered_columns:
                if col not in df_pred.columns:
                    df_pred[col] = ""  # Ajoute colonne vide si manquante
            df_pred = df_pred[ordered_columns]

        # ✅ Sauvegarde CSV final
        df_pred.to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"\n✅ Saved → {out_csv}")

    else:
        print("\n⚠️ No predictions.")

    # 6️⃣ Nettoyage temporaire
    for f in tmp_files:
        try:
            os.remove(f)
        except Exception:
            pass
