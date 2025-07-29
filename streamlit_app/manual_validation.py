# streamlit_app/manual_validation.py

import streamlit as st
import pandas as pd
import os
import random
from PIL import Image

# === Config globale ===
DATA_DIR = "data/cases/npd_case"
PRED_PATH = "data/pred_2/predictions_np.csv"
EXCLUDE_COLS = ["row_id"]

# === Chargement des données (avec cache) ===
@st.cache_data
def load_data():
    df = pd.read_csv(PRED_PATH)
    all_cases = df["row_id"].dropna().unique().tolist()
    columns = [col for col in df.columns if col not in EXCLUDE_COLS]
    return df, all_cases, columns

# === Récupération des médias d’un dossier ===
def get_media(case_path):
    images = [f for f in os.listdir(case_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    videos = [f for f in os.listdir(case_path) if f.lower().endswith('.mp4')]
    return images, videos

# === Affichage d’un média principal (image ou vidéo) ===
def display_media(case_path):
    images, videos = get_media(case_path)
    if images:
        st.image(os.path.join(case_path, images[0]), width=350)
    elif videos:
        st.video(os.path.join(case_path, videos[0]))
    else:
        st.info("Aucun média disponible.")

# === Setup de l’application ===
st.set_page_config(page_title="Validation IA", layout="wide")
pred_df, case_ids, column_names = load_data()

# === Initialisation du state ===
if "step" not in st.session_state:
    st.session_state.step = 0
if "total_correct" not in st.session_state:
    st.session_state.total_correct = 0
if "total_validated" not in st.session_state:
    st.session_state.total_validated = 0
if "max_values" not in st.session_state:
    st.session_state.max_values = 50

# === Choix initial de l'utilisateur ===
if st.session_state.step == 0:
    st.title("🧪 Validation manuelle des prédictions IA")
    st.markdown("Valide les prédictions IA à partir des médias. À chaque étape, 10 prédictions sont proposées pour un média donné.")

    max_possible = len(case_ids) * len(column_names)
    st.session_state.max_values = st.slider(
        "🎯 Choisis combien de **valeurs au total** tu veux valider :",
        min_value=10, max_value=(max_possible // 10) * 10, step=10, value=50
    )

    if st.button("🚀 Démarrer la validation"):
        st.session_state.step = 1
        st.rerun()

# === Étapes de validation ===
elif st.session_state.total_validated < st.session_state.max_values:
    st.markdown(f"### Étape {st.session_state.step} / {st.session_state.max_values // 10}")

    # Choix aléatoire d’un case_id
    case_id = random.choice(case_ids)
    row = pred_df[pred_df["row_id"] == case_id].iloc[0]
    case_path = os.path.join(DATA_DIR, case_id)

    # 10 colonnes aléatoires à valider
    sampled_cols = random.sample(column_names, 10)

    col1, col2 = st.columns([1.1, 1.5])
    with col1:
        display_media(case_path)

    with col2:
        st.markdown(f"#### 📝 Vérification des prédictions pour `{case_id}`")
        form_key = f"form_{st.session_state.step}"
        with st.form(key=form_key):
            correct_count = 0
            for col in sampled_cols:
                value = row[col]
                resp = st.selectbox(
                    f"**{col}** : `{value}`",
                    ["Sélectionner", "Correct", "Incorrect"],
                    key=f"{case_id}_{col}_{st.session_state.step}"
                )
                if resp == "Correct":
                    correct_count += 1

            submitted = st.form_submit_button("✅ Valider et passer au média suivant")
            if submitted:
                st.session_state.total_correct += correct_count
                st.session_state.total_validated += len(sampled_cols)
                st.session_state.step += 1
                st.rerun()

# === Fin : Résultats ===
else:
    st.balloons()
    st.markdown("## 🎉 Validation terminée !")
    score = 100 * st.session_state.total_correct / st.session_state.total_validated
    st.success(f"**Score final : {score:.2f}%**")
    st.markdown(f"- ✅ **{st.session_state.total_correct}** valeurs correctes")
    st.markdown(f"- 🔎 **{st.session_state.total_validated}** valeurs vérifiées")

    if st.button("🔄 Recommencer"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


