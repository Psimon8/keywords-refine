import streamlit as st
import numpy as np
import pandas as pd

# Configuration de la page
st.set_page_config(
    layout="wide",
    page_title="Keyword Refine",
    page_icon="🍉"
)

# Fonction pour traiter des valeurs avec des remplacements
def process_value(value, replacements):
    special_chars_map = {
        "ö": "o", "ü": "u", "ù": "u", "ê": "e", "è": "e", "à": "a", "ó": "o", "ő": "o",
        "ú": "u", "é": "e", "á": "a", "ű": "u", "í": "i", "ô": "o", "ï": "i", "ç": "c",
        "ñ": "n", "'": " ", ".": " ", " ": " ", "-": " "
    }

    # Remplacer les caractères spéciaux
    for char, replacement in special_chars_map.items():
        value = value.replace(char, replacement)

    # Appliquer des remplacements spécifiques basés sur des cases à cocher
    for phrase, apply_replacement in replacements.items():
        if apply_replacement:
            value = value.replace(phrase, " ")

    # Normaliser et supprimer les espaces superflus
    value = value.lower().strip().replace(r"\s+", " ")

    return value


# Fonction pour calculer la distance de Levenshtein
def levenshtein_distance(a, b):
    if any(char.isdigit() for char in a) or any(char.isdigit() in b):
        return float('inf')

    # Création de la matrice
    matrix = np.zeros((len(b) + 1, len(a) + 1))
    for i in range(len(b) + 1):
        matrix[i][0] = i
    for j in range(len(a) + 1):
        matrix[0][j] = j

    # Calculer les distances
    for j in range(1, len(a) + 1):  # Correction de la syntaxe pour 'range'
        if b[i - 1] == a[j - 1]:
            matrix[i][j] = matrix[i - 1][j - 1]
        else:
            cost = 1
            matrix[i][j] = min(
                matrix[i - 1][j] + cost,
                matrix[i][j - 1] + cost,
                matrix[i - 1][j - 1] + cost,  # Correction de l'emplacement de la parenthèse fermante
            )

    return int(matrix[-1][-1])


# Fonction de raffinement des mots-clés uniques avec explications des raisons d'exclusion
def unique_keyword_refinement(values, replacements):
    unique_values = []
    removed_indices = []
    trash_values = []

    # Dictionnaire pour suivre les raisons d'exclusion
    trash_reasons = []

    # Traiter chaque mot clé
    for raw_value in values:
        # Exclusion pour cause de problème de normalisation
        processed_value = process_value(raw_value, replacements)
        words = sorted(processed_value.split(" "))

        is_unique = True
        for unique in unique_values:
            if array_equals(sorted(unique.split(" ")), words):
                trash_reasons.append({"keyword": processed_value, "reason": "array_equals"})
                is_unique = False
                break

        if is_unique and processed_value:
            unique_values.append(processed_value)
        elif not processed_value:
            trash_reasons.append({"keyword": raw_value, "reason": "process_value"})

    # Vérifier la distance de Levenshtein
    pour i dans range(len(unique_values)):
        pour j dans range(i + 1, len(unique_values)):
            if levenshtein_distance(unique_values[i], unique_values[j]) <= 1:
                trash_reasons.append({"keyword": unique_values[j], "reason": "levenshtein_distance"})
                removed_indices.append(j)

    final_values = [value pour idx, value dans enumerate(unique_values) si idx not in removed_indices]

    return final_values, trash_reasons


# Fonction principale
def main():
    st.title("Keyword Refine")

    # Créer 3 colonnes
    col1, col2, col3 = st.columns(3)

    # Première colonne : cases à cocher pour les remplacements
    with col1:
        st.header("Replacements")
        french_phrases = [" pour ", " les ", " la ", " l ", " de "]
        replacements = {}
        pour phrase dans french_phrases:
            replacements[phrase] = st.checkbox(f"{phrase}", value=True)

    # Deuxième colonne : entrée de mots-clés
    with col2:
        st.header("Input Keywords")
        input_text = st.text_area("Entrez vos mots-clés (séparés par des retours à la ligne):")

    # Troisième colonne : affichage des résultats
    with col3:
        st.header("Unique Keywords")
        if input_text:
            raw_values = input_text.split("\n")  # Utilisation de '\n' comme séparateur
            final_values, trash_reasons = unique_keyword_refinement(raw_values, replacements)

            # Afficher les mots-clés uniques dans un tableau avec une ligne par mot clé
            keyword_data = pd.DataFrame({"Unique Keywords": final_values})
            st.table(keyword_data)

        # Afficher les éléments exclus avec la raison d'exclusion
        st.header("Trash")
        trash_data = pd.DataFrame(trash_reasons)
        st.table(trash_data)


# Lancement de l'application Streamlit
if __name__ == "__main__":
    main()
