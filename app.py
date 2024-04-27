import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(
    layout="wide",
    page_title="Keyword Refine",
    page_icon="🍉"
)

def process_value(value, replacements):
    special_chars_map = {
        "ö": "o", "ü": "u", "ù": "u", "ê": "e", "è": "e", "à": "a", "ó": "o", "ő": "o",
        "ú": "u", "é": "e", "á": "a", "ű": "u", "í": "i", "ô": "o", "ï": "i", "ç": "c",
        "ñ": "n", "'": " ", ".": " ", " ": " ", "-": " "
    }

    for char, replacement in special_chars_map.items():
        value = value.replace(char, replacement)

    # Apply specific replacements based on checkboxes
    for phrase, apply_replacement in replacements.items():
        if apply_replacement:
            value = value.replace(phrase, " ")

    # Normalize and trim spaces
    value = value.lower().strip().replace(r"\s+", " ")

    return value


def levenshtein_distance(a, b):
    if any(char.isdigit() for char in a) or any(char.isdigit() for char in b):
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
                cost = 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + cost,
                    matrix[i][j - 1] + cost,
                    matrix[i - 1][j - 1] + cost,
                )

    return int(matrix[-1][-1])


def array_equals(a, b):
    return len(a) == len(b) and all(x == y for x, y in zip(a, b))


def unique_keyword_refinement(values, replacements):
    unique_values = []
    removed_indices = []
    trash_values = []

    for raw_value in values:
        processed_value = process_value(raw_value, replacements)
        words = sorted(processed_value.split(" "))

        is_unique = True
        for unique in unique_values:
            if array_equals(sorted(unique.split(" ")), words):
                is_unique = False
                break

        if is_unique and processed_value:
            unique_values.append(processed_value)

    # Check Levenshtein distance
    for i in range(len(unique_values)):
        for j in range(i + 1, len(unique_values)):
            if levenshtein_distance(unique_values[i], unique_values[j]) <= 1:
                removed_indices.append(j)

    final_values = [value for idx, value in enumerate(unique_values) if idx not in removed_indices]
    trash_values = [unique_values[idx] for idx in removed_indices]

    return final_values, trash_values


def main():
    st.title("Keyword Refine")

    # Create 3 columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.header("Input Keywords")
        input_text = st.text_area("Enter your keywords (comma-separated):")

    with col1:
            st.header("Unique Keywords")
            st.write(", ".join(final_values))
         
    with col3:
        st.header("Replacements")
        # Define specific French phrases and create checkboxes
        french_phrases = [" pour ", " les ", " la ", " l ", " de ", " en ", " d ", " du ", " le "]
        replacements = {}
        for phrase in french_phrases:
            replacements[phrase] = st.checkbox(f"'{phrase}'?", value=True)

    if input_text:
        raw_values = input_text.split(",")

        final_values, trash_values = unique_keyword_refinement(raw_values, replacements)

        with col2:
            st.header("Trash")
            st.write(", ".join(trash_values))

        with col1:
            st.header("Unique Keywords")
            st.write(", ".join(final_values))


if __name__ == "__main__":
    main()
