import streamlit as st
import numpy as np
import pandas as pd
import re
from io import BytesIO

# Page configuration
st.set_page_config(
    layout="wide",
    page_title="Keyword Refine",
    page_icon="🎯"
)

def export_to_excel(df):
    """Export DataFrame to Excel bytes with error handling"""
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()
    except Exception as e:
        st.error(f"Erreur d'export Excel: {str(e)}")
        return None

def process_value(value, replacements, case_sensitive=False):
    """Process a single value with special character handling"""
    special_chars_map = {
        "ö": "o", "ü": "u", "ù": "u", "ê": "e", "è": "e", "à": "a",
        "ó": "o", "ő": "o", "ú": "u", "é": "e", "á": "a", "ű": "u",
        "í": "i", "ô": "o", "ï": "i", "ç": "c", "ñ": "n", "'": " ",
        ".": " ", " ": " ", "-": " ", "â": "a", "î": "i"
    }

    original_value = value

    # Apply case sensitivity
    if not case_sensitive:
        value = value.lower()

    # Replace special characters
    for key, replacement in special_chars_map.items():
        value = value.replace(key, replacement)

    # Apply specific replacements
    for phrase, apply_replacement in replacements.items():
        if apply_replacement:
            value = value.replace(phrase, " ")

    # Normalize spaces
    value = re.sub(r"\s+", " ", value).strip()

    return value, original_value

def levenshtein_distance(a, b):
    """Calculate Levenshtein distance between two strings"""
    if any(c.isdigit() for c in a) or any(c.isdigit() for c in b):
        return float('inf')

    matrix = np.zeros((len(b) + 1, len(a) + 1))
    for i in range(len(b) + 1):
        matrix[i][0] = i
    for j in range(len(a) + 1):
        matrix[0][j] = j

    for i in range(1, len(b) + 1):
        for j in range(1, len(a) + 1):
            if b[i - 1] == a[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1]
            else:
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + 1
                )

    return int(matrix[-1][-1])

def array_equals(a, b):
    """Compare two arrays for equality"""
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))

def get_reason_description(reason_code):
    """Convert reason codes to human-readable descriptions"""
    reasons = {
        "special_chars_replaced": "Caractères spéciaux remplacés",
        "array_equals": "Mot-clé en double",
        "process_value": "Mot-clé vide après traitement",
        "too_short": "Mot-clé trop court",
        "levenshtein_distance": "Mots similaires"
    }
    return reasons.get(reason_code, reason_code)

def unique_keyword_refinement(values, replacements, min_length=1, levenshtein_threshold=1, case_sensitive=False):
    """Refine keywords with detailed tracking of removals"""
    unique_values = []
    removed_indices = []
    trash_reasons = []
    removed_keys_set = set()

    # Filter out empty values
    values = [v.strip() for v in values if v.strip()]

    for raw_value in values:
        # Check minimum length
        if len(raw_value) < min_length:
            trash_reasons.append({
                "conserved": "",
                "removed": raw_value,
                "reason": "too_short"
            })
            continue

        processed_value, original_value = process_value(raw_value, replacements, case_sensitive)
        words = sorted(processed_value.split(" "))

        # Track special characters replacement
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

    # Check Levenshtein distance
    for i in range(len(unique_values)):
        for j in range(i + 1, len(unique_values)):
            distance = levenshtein_distance(unique_values[i], unique_values[j])
            if distance <= levenshtein_threshold:
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

def main():
    st.title("🎯 Keyword Refine")

    # Instructions
    with st.expander("📖 Instructions", expanded=False):
        st.markdown("""
        ### Comment utiliser Keyword Refine:
        1. **Entrée**: Saisissez vos mots-clés, un par ligne
        2. **Paramètres**: Ajustez les options dans la barre latérale
        3. **Résultats**: Visualisez les mots-clés raffinés et les éléments supprimés
        4. **Export**: Téléchargez les résultats au format souhaité
        """)

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Paramètres")

        min_length = st.number_input("Longueur minimum", min_value=1, value=1)
        levenshtein_threshold = st.number_input("Seuil de similarité", min_value=1, max_value=5, value=1)
        case_sensitive = st.checkbox("Sensible à la casse", value=False)

        st.subheader("Phrases à supprimer")
        french_phrases = [" for ", " les ", " la ", " l ", " de "]
        replacements = {}
        for phrase in french_phrases:
            replacements[phrase] = st.checkbox(phrase.strip(), value=True)

    # Main content
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.header("📝 Mots-clés d'entrée")
        input_text = st.text_area(
            "Entrez vos mots-clés (un par ligne):",
            height=300,
            help="Entrez chaque mot-clé sur une nouvelle ligne"
        )

    if input_text:
        raw_values = [v for v in input_text.split("\n") if v.strip()]
        final_values, trash_reasons = unique_keyword_refinement(
            raw_values,
            replacements,
            min_length,
            levenshtein_threshold,
            case_sensitive
        )

        with col2:
            st.header("✨ Mots-clés raffinés")
            st.metric("Total mots-clés", len(final_values))
            keyword_data = pd.DataFrame({"Mots-clés": final_values})
            st.dataframe(keyword_data, height=300)

            # Export buttons
            col2a, col2b = st.columns(2)
            with col2a:
                csv = keyword_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Télécharger CSV",
                    csv,
                    "mots_cles_raffines.csv",
                    "text/csv",
                    key='download-csv'
                )
            with col2b:
                excel_file = export_to_excel(keyword_data)
                if excel_file:
                    st.download_button(
                        "📥 Télécharger Excel",
                        excel_file,
                        "mots_cles_raffines.xlsx",
                        key='download-excel'
                    )

        with col3:
            st.header("🗑️ Éléments supprimés")
            st.metric("Éléments supprimés", len(trash_reasons))
            if trash_reasons:
                trash_data = pd.DataFrame(trash_reasons)
                trash_data['reason'] = trash_data['reason'].apply(get_reason_description)
                trash_data.columns = ["Conservé", "Supprimé", "Raison"]
                st.dataframe(trash_data, height=300)
            else:
                st.info("Aucun mot-clé supprimé")

if __name__ == "__main__":
    main()
