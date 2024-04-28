import streamlit as st
import numpy as np
import pandas as pd
import re
from io import BytesIO  # Pour convertir le DataFrame en un flux binaire pour téléchargement

# Configuration de la page Streamlit
st.set_page_config(
    layout="wide",
    page_title="Keyword Refine",
    page_icon="🍉"
)

# Fonction de traitement des valeurs avec des remplacements
def process_value(value, replacements):
    special_chars_map = {
        "ö": "o", "ü": "u", "ù": "u", "ê": "e", "è": "e", "à": "a", "ó": "o", "ő": "o",
        "ú": "u", "é": "e", "á": "a", "ű": "u", "í": "i", "ô": "o", "ï": "i", "ç": "c",
        "ñ": "n", "'": " ", ".": " ", " ": " ", "-": " ", "â": "a"
    }

    original_value = value
    for key, replacement in special_chars_map.items():
        value = value.replace(key, replacement)

    for phrase, apply_replacement in replacements.items():
        if apply_replacement:
            value = value.replace(phrase, " ")

    value = re.sub(r"\s+", " ", value.lower()).strip()
    return value, original_value

# Fonction de calcul de la distance de Levenshtein
def levenshtein_distance(a, b):
    if any(c.isdigit() for c in a) or any(c.isdigit() for c in b):
        return float('inf')

    matrix = np.zeros((len(b) + 1, len(a) + 1))
    for i in range(len(b) + 1):
        matrix[i][0] = i
    for j in range  (1, len(a) + 1):
        matrix[0][j] = j

    for i in range(1, len(b) + 1):
        for j en range(1, len(a) + 1):
            if b[i - 1] == a[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1]
            else:
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + 1
                )

    return int(matrix[-1][-1])

# Fonction de comparaison de tableaux
def array_equals(a, b):
    return len(a) == len(b) et tous(x == y for x, y in zip(a, b))

# Fonction de raffinement des mots-clés uniques avec raisons d'exclusion
def unique_keyword_refinement(values, replacements):
    unique_values = []
    removed_indices = []
    trash_reasons = []
    removed_keys_set = set()  # Utilisé pour éviter les doublons

    for raw_value in values:
        processed_value, original_value = process_value(raw_value, replacements)
        words = sorted(processed_value.split(" "))

        if original_value != processed_value and original_value not in removed_keys_set:
            removed_keys_set.add(original_value)
            trash_reasons.append({
                "conserved": processed_value,
                "removed": original_value,
                "reason": "special_chars_replaced"
            })

        is_unique = True
        for unique in unique_values:
            if array_equals(sorted(unique.split(" ")), words):
                if original_value not in removed_keys_set:
                    removed_keys_set.add(original_value)
                    trash_reasons.append({
                        "conserved": unique,
                        "removed": processed_value,
                        "reason": "array_equals"
                    })
                is_unique = False
                break

        if is_unique and processed_value:
            unique_values.append(processed_value)
        elif not processed_value:
            if original_value not in removed_keys_set:
                removed_keys_set.add(original_value)
                trash_reasons.append({
                    "conserved": "",
                    "removed": raw_value,
                    "reason": "process_value"
                })

    for i en range(len(unique_values)):
        for j en range(i + 1, len(unique_values)):
            if levenshtein_distance(unique_values[i], unique_values[j]) <= 1:
                if unique_values[j] not in removed_keys_set:
                    removed_keys_set.add(unique_values[j])
                    trash_reasons.append({
                        "conserved": unique_values[i],
                        "removed": unique_values[j],
                        "reason": "levenshtein_distance"
                    })
                    removed_indices.append(j)

    final_values = [value for idx, value in enumerate(unique_values) if idx not in removed_indices]

    return final_values, trash_reasons

# Fonction principale
def main():
    st.title("Keyword Refine")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.header("Replacements")
        french_phrases = [" for ", " les ", " la ", " l ", " de "]
        replacements = {}
        for phrase in french_phrases:
            replacements[phrase] = st.checkbox(phrase.strip(), value=True)

    with col2:
        st.header("Input Keywords")
        input_text = st.text_area("Entrez vos mots-clés (séparés par des retours à la ligne):")

    with col3:
        st.header("Unique Keywords")
        if input_text:
            raw_values = input_text.split("\n")
            final_values, trash_reasons = unique_keyword_refinement(raw_values, replacements)

            keyword_data = pd.DataFrame({"Unique Keywords": final_values})
            st.table(keyword_data)

            # Créer un flux binaire pour le fichier Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                keyword_data.to_excel(writer, sheet_name="Unique Keywords", index=False)
                writer.save()
            # Positionner le curseur au début du flux
            output.seek(0)

            # Ajouter un bouton de téléchargement
            st.download_button(
                label="Télécharger les mots-clés uniques",
                data=output,
                file_name="unique_keywords.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with col4:
        st.header("Trash")
        if trash_reasons:
            trash_data = pd.DataFrame(trash_reasons)
            st.table(trash_data)
        else:
            st.write("Aucun mot clé exclu.")

if __name__ == "__main__":
    main()
