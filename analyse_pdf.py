import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from io import BytesIO
import fitz  # PyMuPDF
import openai
import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

# Configuration Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

# Paramètres
MAX_DEPTH = 3
MAX_PAGES = 3


def azure_openai_chat_completion(prompt):
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version=2023-05-15"
    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def analyze_pdf_with_llm(text):
    prompt = f"""
Tu es un assistant chargé d’évaluer si un document PDF est pertinent pour la plateforme Abhatoo, qui collecte des documents de littérature grise institutionnelle.

Voici un extrait du document :

\"\"\"{text}\"\"\"

Réponds strictement au format suivant :
Pertinent : <OUI ou NON>
Langue : <Français, Arabe ou Anglais>
Thématique : <un mot-clé parmi Éducation, Santé, Emploi, Énergie, Environnement, Transport, Urbanisme, Agriculture, Industrie, Développement durable, Gouvernance, Inégalités, Numérique, etc.>

Critères de pertinence :
- Le document traite de sujets liés au développement social, économique, durable, à la recherche scientifique, aux politiques publiques ou aux cadres stratégiques.
- Le contenu est utile pour la recherche, la compréhension ou l’analyse des politiques publiques.
- Il est produit par une institution publique, semi-publique ou par une institution étrangère à condition que le sujet concerne le Maroc (ex. : ministère, établissement public, collectivité territoriale...).
- Ce n’est pas une brochure promotionnelle, un simple communiqué, un guide technique ou un article de presse.

Exemple de réponse attendue :
Pertinent : OUI
Langue : Français
Thématique : Énergie

Merci de répondre uniquement selon le format spécifié.
"""

    try:
        response = azure_openai_chat_completion(prompt)
        result = {"pertinent": False, "langue": "Inconnue", "thematique": "Inconnue"}

        for line in response.strip().splitlines():
            if "pertinent" in line.lower():
                result["pertinent"] = "OUI" in line.upper()
            elif "langue" in line.lower():
                result["langue"] = line.split(":")[-1].strip()
            elif "thématique" in line.lower():
                result["thematique"] = line.split(":")[-1].strip()
        return result
    except Exception as e:
        print(f"❌ Erreur Azure OpenAI : {e}")
        return {"pertinent": False, "langue": "Erreur", "thematique": "Erreur"}


def extract_preview_from_pdf(pdf_url, max_pages=3):
    """
    Extrait un aperçu du texte d'un PDF depuis une URL
    
    Args:
        pdf_url (str): URL du PDF
        max_pages (int): Nombre maximum de pages à extraire
    
    Returns:
        str: Texte extrait ou None si erreur
    """
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Ouvrir le PDF depuis les bytes
        pdf_document = fitz.open(stream=response.content, filetype="pdf")
        text_content = ""
        
        # Extraire le texte des premières pages
        pages_to_extract = min(max_pages, len(pdf_document))
        for page_num in range(pages_to_extract):
            page = pdf_document.load_page(page_num)
            text_content += page.get_text()
        
        pdf_document.close()
        
        # Nettoyer et limiter le texte
        text_content = text_content.strip()
        if len(text_content) < 50:
            return None
            
        return text_content[:3000]  # Limiter pour OpenAI
        
    except Exception as e:
        print(f"❌ Erreur extraction PDF {pdf_url}: {e}")
        return None

def save_to_file(pdf_entries, filename="pdf_valides.json"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(pdf_entries, f, ensure_ascii=False, indent=2)
        print(f"✅ PDFs pertinents enregistrés dans : {filename}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde JSON : {e}")

if __name__ == "__main__":
    # url_de_depart = "https://www.finances.gov.ma/"
    # print("🕸️ Démarrage du crawl...")
    # tous_les_pdfs = recursive_pdf_crawler(url_de_depart, max_depth=MAX_DEPTH)

    # print(f"🔍 {len(tous_les_pdfs)} PDF trouvés. Analyse en cours...\n")
    # Lecture des liens PDF depuis le fichier
    with open("liens_pdfs.txt", "r", encoding="utf-8") as f:
        tous_les_pdfs = [line.strip() for line in f.readlines() if line.strip()]

    visited_links = set()
    pdf_links_valides = []
    for pdf_url in tous_les_pdfs:
        if pdf_url in visited_links:
            continue

        visited_links.add(pdf_url)
        preview_text = extract_preview_from_pdf(pdf_url, max_pages=3)

        if preview_text:
            metadata = analyze_pdf_with_llm(preview_text)
            if metadata["pertinent"]:
                print(f"✅ PDF retenu : {pdf_url}")
                print(f"   Langue     : {metadata['langue']}")
                print(f"   Thématique : {metadata['thematique']}\n")
                pdf_links_valides.append({
                    "url": pdf_url,
                    "langue": metadata["langue"],
                    "thematique": metadata["thematique"]
                })
            else:
                print(f"⛔ PDF rejeté : {pdf_url}\n")
        else:
            print(f"⚠️ Aucun texte extrait : {pdf_url}\n")

    if pdf_links_valides:
        save_to_file(pdf_links_valides, "pdf_valides.json")
    else:
        print("❌ Aucun PDF pertinent trouvé.")
