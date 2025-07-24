import sqlite3
import json
from pathlib import Path
from docx import Document
import os
from langdetect import detect
from transformers import pipeline

# Initialiser le résumé avec HuggingFace Transformers (ou utiliser ton propre modèle)
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = '\n'.join([para.text for para in doc.paragraphs])
        return full_text.strip()
    except Exception as e:
        print(f"Erreur de lecture: {file_path} -> {e}")
        return None

def analyze_document(file_path):
    text = extract_text_from_docx(file_path)
    if not text:
        return {
            "summary": None,
            "language": "inconnu",
            "theme": "Inconnu",
            "extraction_success": False
        }

    # Génération du résumé
    try:
        input_length = len(text.split())
        max_len = min(130, int(input_length * 0.8)) if input_length > 40 else input_length
        min_len = min(30, max_len - 1) if max_len > 30 else max(5, max_len // 2)

        summary = summarizer(
            text[:1000],
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )[0]["summary_text"]

    except Exception as e:
        print(f"Erreur lors du résumé : {e}")
        summary = "Résumé non généré."

    # Détection de la langue
    try:
        language = detect(text)
    except Exception:
        language = "inconnu"

    # Détermination du thème (simplifiée)
    theme = "Inconnu"
    lowered = text.lower()
    if "finance" in lowered:
        theme = "Finance"
    elif "agriculture" in lowered:
        theme = "Agriculture"
    elif "économie" in lowered or "économique" in lowered:
        theme = "Économie"

    # Retour du résultat complet
    return {
        "summary": summary,
        "language": language,
        "theme": theme,
        "extraction_success": True
    }


def main():
    db_path = "db.sqlite3"
    result_list = []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT filename, file_path FROM scraper_wordsdocument")
    rows = cursor.fetchall()

    for filename, file_path in rows:
        if not os.path.exists(file_path):
            print(f"Fichier manquant: {file_path}")
            continue

        analysis = analyze_document(file_path)
        if analysis:
            result = {
                "filename": filename,
                "file_path": file_path,
                **analysis
            }
            result_list.append(result)

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Analyse terminée. Résultats enregistrés dans result.json")

if __name__ == "__main__":
    main()
