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
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def process_value(value, replacements, case_sensitive=False):
    special_chars_map = {
        "ö": "o", "ü": "u", "ù": "u", "ê": "e", "è": "e", "à": "a", "ó": "o", "ő": "o",
        "ú": "u", "é": "e", "á": "a", "ű": "u", "í": "i", "ô": "o", "ï": "i", "ç": "c",
        "ñ": "n", "'": " ", ".": " ", " ": " ", "-": " ", "â": "a", "î": "i"
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
    if any(c.isdigit() for c in a) or any(c.isdigit() for c in b):
        return float('inf')

    matrix = np.zeros((len(b) + 1, len(a) + 1))
    for i in range(len(b) + 1):
        matrix[i][0] = i
    for j in range(1, len(a) + 1):
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
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))

def unique_keyword_refinement(values, replacements, min_length=1, levenshtein_threshold=1, case_sensitive=False):
    unique_values = []
    removed_indices = []
    trash_reasons = []
    removed_keys_set = set()

    # Filter out empty values and those below minimum length
    values = [v.strip() for v in values if v.strip()]

    for raw_value in values:
        if len(raw_value) < min_length:
            trash_reasons.append({
                "conserved": "",
                "removed": raw_value,
                "reason": "too_short"
            })
            continue

        processed_value, original_value = process_value(raw_value, replacements, case_sensitive)
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
                        "reason": "duplicate"
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
                    "reason": "empty_after_processing"
                })

    # Check Levenshtein distance
    for i in range(len(unique_values)):
        for j in range(i + 1, len(unique_values)):
            if levenshtein_distance(unique_values[i], unique_values[j]) <= levenshtein_threshold:
                if unique_values[j] not in removed_keys_set:
                    removed_keys_set.add(unique_values[j])
                    trash_reasons.append({
                        "conserved": unique_values[i],
                        "removed": unique_values[j],
                        "reason": f"similar (distance={levenshtein_threshold})"
                    })
                    removed_indices.append(j)

    final_values = [value for idx, value in enumerate(unique_values) if idx not in removed_indices]

    return final_values, trash_reasons

def main():
    st.title("🎯 Keyword Refine")

    # Instructions
    with st.expander("📖 Instructions", expanded=False):
        st.markdown("""
        ### How to use Keyword Refine:
        1. **Input**: Enter your keywords, one per line
        2. **Settings**: Adjust the processing options in the sidebar
        3. **Results**: View refined keywords and removed items
        4. **Export**: Download results in your preferred format

        ### Features:
        - Removes duplicates and similar keywords
        - Handles special characters
        - Customizable filtering options
        - Export capabilities
        """)

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")

        min_length = st.number_input("Minimum keyword length", min_value=1, value=1)
        levenshtein_threshold = st.number_input("Similarity threshold", min_value=1, max_value=5, value=1)
        case_sensitive = st.checkbox("Case sensitive", value=False)

        st.subheader("Phrases to remove")
        french_phrases = [" for ", " les ", " la ", " l ", " de "]
        replacements = {}
        for phrase in french_phrases:
            replacements[phrase] = st.checkbox(phrase.strip(), value=True)

    # Main content
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.header("📝 Input Keywords")
        input_text = st.text_area(
            "Enter keywords (one per line):",
            height=300,
            help="Enter each keyword on a new line"
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
            st.header("✨ Refined Keywords")
            st.metric("Total Keywords", len(final_values))
            keyword_data = pd.DataFrame({"Keywords": final_values})
            st.dataframe(keyword_data, height=300)

            # Export buttons
            col2a, col2b = st.columns(2)
            with col2a:
                csv = keyword_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "refined_keywords.csv",
                    "text/csv",
                    key='download-csv'
                )
            with col2b:
                excel_file = export_to_excel(keyword_data)
                st.download_button(
                    "📥 Download Excel",
                    excel_file,
                    "refined_keywords.xlsx",
                    key='download-excel'
                )

        with col3:
            st.header("🗑️ Removed Items")
            st.metric("Removed Items", len(trash_reasons))
            if trash_reasons:
                trash_data = pd.DataFrame(trash_reasons)
                st.dataframe(trash_data, height=300)
            else:
                st.info("No keywords were removed")

if __name__ == "__main__":
    main()
