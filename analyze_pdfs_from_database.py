#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse des PDFs depuis la base de données

Ce script :
1. Supprime toutes les données de la table scraper_wordsdocument
2. Met à jour le champ site_web dans scraper_scrapedpdf avec le nom du site web
3. Analyse les PDFs directement depuis scraper_scrapedpdf avec Azure OpenAI
4. Sauvegarde les résultats dans un fichier JSON

Auteur: Assistant IA
Date: 2025-07-25
"""

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_analysis.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

# Vérification des variables d'environnement
if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME]):
    logger.error("❌ Variables d'environnement Azure OpenAI manquantes")
    sys.exit(1)

# Configuration
DATABASE_PATH = 'db.sqlite3'
MAX_PAGES_EXTRACT = 3  # Nombre de pages à extraire pour l'analyse
MAX_TOKENS = 1000  # Tokens maximum pour OpenAI
RESULT_FILE = 'scraper/static/data/pdf_analysis_results.json'

def azure_openai_chat_completion(prompt):
    """
    Appel à l'API Azure OpenAI pour l'analyse de texte
    
    Args:
        prompt (str): Le prompt à envoyer à OpenAI
    
    Returns:
        str: La réponse de l'API
    """
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version=2023-05-15"
    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.3,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erreur API Azure OpenAI: {e}")
        return None
    except KeyError as e:
        logger.error(f"❌ Erreur format réponse OpenAI: {e}")
        return None

def extract_text_from_pdf(file_path, max_pages=3):
    """
    Extrait le texte des premières pages d'un PDF
    
    Args:
        file_path (str): Chemin vers le fichier PDF
        max_pages (int): Nombre maximum de pages à extraire
    
    Returns:
        str: Texte extrait ou None si erreur
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Fichier non trouvé: {file_path}")
            return None
            
        doc = fitz.open(file_path)
        text_content = ""
        
        # Extraire le texte des premières pages
        pages_to_extract = min(max_pages, len(doc))
        for page_num in range(pages_to_extract):
            page = doc.load_page(page_num)
            text_content += page.get_text()
        
        doc.close()
        
        # Nettoyer le texte
        text_content = text_content.strip()
        if len(text_content) < 50:  # Texte trop court
            return None
            
        return text_content[:4000]  # Limiter la taille pour OpenAI
        
    except Exception as e:
        logger.error(f"❌ Erreur extraction PDF {file_path}: {e}")
        return None

def analyze_pdf_with_openai(text_content):
    """
    Analyse le contenu d'un PDF avec Azure OpenAI
    
    Args:
        text_content (str): Contenu textuel du PDF
    
    Returns:
        dict: Résultats de l'analyse
    """
    prompt = f"""
Tu es un assistant spécialisé dans l'analyse de documents institutionnels marocains.

Analyse le texte suivant et fournis une réponse STRICTEMENT au format JSON suivant :

{{
  "pertinent": true/false,
  "langue": "Français/Arabe/Anglais/Mixte",
  "thematique": "Agriculture/Économie/Éducation/Santé/Environnement/Gouvernance/Finance/Industrie/Transport/Autre",
  "confiance": "Élevée/Moyenne/Faible",
  "resume": "Résumé en 2-3 phrases maximum"
}}

Critères de pertinence :
- Document officiel ou institutionnel
- Contenu lié aux politiques publiques, développement, recherche
- Produit par une institution publique ou organisation reconnue
- Utile pour la recherche ou l'analyse des politiques

Texte à analyser :
{text_content}

Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire.
"""

    try:
        response = azure_openai_chat_completion(prompt)
        if not response:
            return {
                "pertinent": False,
                "langue": "Erreur",
                "thematique": "Erreur",
                "confiance": "Faible",
                "resume": "Erreur lors de l'analyse"
            }
        
        # Nettoyer la réponse pour extraire le JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:-3]
        elif response.startswith('```'):
            response = response[3:-3]
        
        # Parser le JSON
        result = json.loads(response)
        
        # Valider les champs requis
        required_fields = ['pertinent', 'langue', 'thematique', 'confiance', 'resume']
        for field in required_fields:
            if field not in result:
                result[field] = "Inconnu"
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erreur parsing JSON OpenAI: {e}")
        logger.error(f"Réponse reçue: {response}")
        return {
            "pertinent": False,
            "langue": "Erreur",
            "thematique": "Erreur",
            "confiance": "Faible",
            "resume": "Erreur de format de réponse"
        }
    except Exception as e:
        logger.error(f"❌ Erreur analyse OpenAI: {e}")
        return {
            "pertinent": False,
            "langue": "Erreur",
            "thematique": "Erreur",
            "confiance": "Faible",
            "resume": "Erreur lors de l'analyse"
        }

def clean_wordsdocument_table(conn):
    """
    Supprime toutes les données de la table scraper_wordsdocument
    
    Args:
        conn: Connexion à la base de données
    """
    try:
        cursor = conn.cursor()
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scraper_wordsdocument'
        """)
        
        if cursor.fetchone():
            # Compter les enregistrements avant suppression
            cursor.execute("SELECT COUNT(*) FROM scraper_wordsdocument")
            count_before = cursor.fetchone()[0]
            
            # Supprimer tous les enregistrements
            cursor.execute("DELETE FROM scraper_wordsdocument")
            conn.commit()
            
            logger.info(f"✅ Table scraper_wordsdocument nettoyée: {count_before} enregistrements supprimés")
        else:
            logger.info("ℹ️ Table scraper_wordsdocument non trouvée")
            
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage table wordsdocument: {e}")
        conn.rollback()

def update_site_web_field(conn):
    """
    Met à jour le champ site_web dans scraper_scrapedpdf avec le nom du site web
    
    Args:
        conn: Connexion à la base de données
    """
    try:
        cursor = conn.cursor()
        
        # Mettre à jour le champ site_web avec le nom du site web
        cursor.execute("""
            UPDATE scraper_scrapedpdf 
            SET site_web = (
                SELECT w.name 
                FROM scraper_website w 
                WHERE w.id = scraper_scrapedpdf.website_id
            )
            WHERE website_id IS NOT NULL
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"✅ Champ site_web mis à jour pour {updated_count} enregistrements")
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour site_web: {e}")
        conn.rollback()

def load_existing_results(filename=RESULT_FILE):
    """
    Charge les résultats existants depuis le fichier JSON
    
    Args:
        filename (str): Nom du fichier JSON
    
    Returns:
        dict: Dictionnaire des résultats existants avec l'ID comme clé
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Convertir en dictionnaire avec l'ID comme clé
            existing_results = {result['id']: result for result in results}
            logger.info(f"📂 {len(existing_results)} résultats existants chargés")
            return existing_results
        else:
            logger.info("📂 Aucun fichier de résultats existant trouvé")
            return {}
    except Exception as e:
        logger.error(f"❌ Erreur chargement résultats existants: {e}")
        return {}

def get_pdfs_to_analyze(conn, only_new=False):
    """
    Récupère la liste des PDFs à analyser depuis la base de données
    
    Args:
        conn: Connexion à la base de données
        only_new (bool): Si True, ne traite que les nouveaux PDFs non analysés
    
    Returns:
        list: Liste des PDFs avec leurs métadonnées
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id,
                p.title,
                p.file_path,
                p.url,
                p.site_web,
                w.name as website_name,
                p.downloaded_at
            FROM scraper_scrapedpdf p
            LEFT JOIN scraper_website w ON p.website_id = w.id
            ORDER BY p.downloaded_at DESC
        """)
        
        pdfs = []
        for row in cursor.fetchall():
            pdfs.append({
                'id': row[0],
                'title': row[1],
                'file_path': row[2],
                'url': row[3],
                'site_web': row[4],
                'website_name': row[5],
                'downloaded_at': row[6]
            })
        
        # Si only_new est True, filtrer les PDFs déjà analysés
        if only_new:
            existing_results = load_existing_results()
            pdfs = [pdf for pdf in pdfs if pdf['id'] not in existing_results]
            logger.info(f"📊 {len(pdfs)} nouveaux PDFs à analyser (sur {len(pdfs) + len(existing_results)} total)")
        else:
            logger.info(f"📊 {len(pdfs)} PDFs trouvés dans la base de données")
        
        return pdfs
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération PDFs: {e}")
        return []

def save_results_to_json(results, filename=RESULT_FILE, merge_with_existing=False):
    """
    Sauvegarde les résultats dans un fichier JSON
    
    Args:
        results (list): Liste des résultats d'analyse
        filename (str): Nom du fichier de sortie
        merge_with_existing (bool): Si True, fusionne avec les résultats existants
    """
    try:
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        final_results = results
        
        if merge_with_existing:
            # Charger les résultats existants
            existing_results = load_existing_results(filename)
            
            # Convertir les nouveaux résultats en dictionnaire
            new_results_dict = {result['id']: result for result in results}
            
            # Fusionner (les nouveaux écrasent les anciens)
            existing_results.update(new_results_dict)
            
            # Convertir en liste
            final_results = list(existing_results.values())
            
            logger.info(f"📊 Fusion: {len(results)} nouveaux + {len(existing_results) - len(results)} existants = {len(final_results)} total")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"✅ Résultats sauvegardés dans {filename}")
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde JSON: {e}")

def main(only_new=False, skip_cleanup=False):
    """
    Fonction principale
    
    Args:
        only_new (bool): Si True, ne traite que les nouveaux PDFs non analysés
        skip_cleanup (bool): Si True, ignore le nettoyage de la table wordsdocument
    """
    mode_text = "nouveaux PDFs" if only_new else "tous les PDFs"
    logger.info(f"🚀 Démarrage de l'analyse des {mode_text} depuis la base de données")
    
    # Vérifier que la base de données existe
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"❌ Base de données non trouvée: {DATABASE_PATH}")
        return
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(DATABASE_PATH)
        logger.info("✅ Connexion à la base de données établie")
        
        # Étape 1: Nettoyer la table scraper_wordsdocument (optionnel)
        if not skip_cleanup:
            logger.info("\n=== Étape 1: Nettoyage de la table scraper_wordsdocument ===")
            clean_wordsdocument_table(conn)
        else:
            logger.info("\n=== Étape 1: Nettoyage ignoré ===")
        
        # Étape 2: Mettre à jour le champ site_web
        logger.info("\n=== Étape 2: Mise à jour du champ site_web ===")
        update_site_web_field(conn)
        
        # Étape 3: Récupérer les PDFs à analyser
        logger.info("\n=== Étape 3: Récupération des PDFs ===")
        pdfs = get_pdfs_to_analyze(conn, only_new=only_new)
        
        if not pdfs:
            if only_new:
                logger.info("✅ Aucun nouveau PDF à analyser")
            else:
                logger.warning("⚠️ Aucun PDF trouvé dans la base de données")
            return
        
        # Étape 4: Analyser les PDFs
        logger.info(f"\n=== Étape 4: Analyse de {len(pdfs)} PDFs ===")
        results = []
        processed = 0
        errors = 0
        
        for i, pdf in enumerate(pdfs, 1):
            logger.info(f"\n📄 [{i}/{len(pdfs)}] Analyse: {pdf['title']}")
            
            # Construire le chemin complet du fichier
            file_path = pdf['file_path']
            if not os.path.isabs(file_path):
                # Si le chemin n'est pas absolu, le construire
                file_path = os.path.join(os.getcwd(), file_path)
            
            # Extraire le texte du PDF
            text_content = extract_text_from_pdf(file_path, MAX_PAGES_EXTRACT)
            
            if not text_content:
                logger.warning(f"⚠️ Impossible d'extraire le texte de {pdf['title']}")
                errors += 1
                continue
            
            # Analyser avec OpenAI
            analysis = analyze_pdf_with_openai(text_content)
            
            # Préparer le résultat
            result = {
                'id': pdf['id'],
                'title': pdf['title'],
                'file_path': pdf['file_path'],
                'url': pdf['url'],
                'site_web': pdf['site_web'] or pdf['website_name'],
                'downloaded_at': pdf['downloaded_at'],
                'analysis': analysis,
                'text_length': len(text_content),
                'analyzed_at': datetime.now().isoformat()
            }
            
            results.append(result)
            processed += 1
            
            # Afficher le résultat
            if analysis['pertinent']:
                logger.info(f"✅ PDF pertinent - Langue: {analysis['langue']}, Thème: {analysis['thematique']}")
            else:
                logger.info(f"⛔ PDF non pertinent")
        
        # Étape 5: Sauvegarder les résultats
        logger.info("\n=== Étape 5: Sauvegarde des résultats ===")
        save_results_to_json(results, merge_with_existing=only_new)
        
        # Statistiques finales
        pertinents = sum(1 for r in results if r['analysis']['pertinent'])
        logger.info(f"\n=== RÉSUMÉ ===")
        logger.info(f"📊 PDFs traités: {processed}")
        logger.info(f"✅ PDFs pertinents: {pertinents}")
        logger.info(f"⛔ PDFs non pertinents: {processed - pertinents}")
        logger.info(f"❌ Erreurs: {errors}")
        logger.info(f"📁 Résultats sauvegardés dans: {RESULT_FILE}")
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("🔒 Connexion à la base de données fermée")

if __name__ == "__main__":
    main()