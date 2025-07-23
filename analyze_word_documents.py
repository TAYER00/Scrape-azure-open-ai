#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour analyser les documents Word avec Azure OpenAI
Extrait le contenu, détermine la langue et le thème, puis sauvegarde dans un fichier result
"""

import os
import sys
import django
import json
from datetime import datetime
from docx import Document
from openai import AzureOpenAI
import logging

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_scraper.settings')
django.setup()

from scraper.models import PDFDocument
from django.conf import settings

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_docx(file_path):
    """
    Extrait le texte d'un fichier Word (.docx)
    """
    try:
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text.strip())
        return '\n'.join(text)
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte de {file_path}: {e}")
        return None

def analyze_with_openai(content, filename):
    """
    Analyse le contenu avec Azure OpenAI pour déterminer la langue et le thème
    """
    try:
        client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        # Limiter le contenu pour éviter les erreurs de token
        content_preview = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""
Analyse ce document et réponds UNIQUEMENT au format JSON suivant :
{{
    "langue": "[français/arabe/anglais/autre]",
    "theme": "[économie/finance/agriculture/politique/juridique/autre]",
    "confiance": "[Élevé/Moyen/Faible]"
}}

Contenu du document "{filename}":
{content_preview}
"""
        
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé dans l'analyse de documents. Réponds uniquement en JSON valide."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Nettoyer la réponse pour extraire le JSON
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].strip()
        
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            logger.warning(f"Réponse OpenAI non-JSON pour {filename}: {result_text}")
            return {
                "langue": "Non déterminé",
                "theme": "Non déterminé", 
                "confiance": "Faible"
            }
            
    except Exception as e:
        logger.error(f"Erreur OpenAI pour {filename}: {e}")
        return {
            "langue": "Erreur",
            "theme": "Erreur",
            "confiance": "Faible"
        }

def main():
    """
    Fonction principale pour analyser tous les documents Word
    """
    logger.info("Début de l'analyse des documents Word avec Azure OpenAI")
    
    # Récupérer tous les documents Word non traités
    word_documents = PDFDocument.objects.filter(
        filename__iendswith='.docx',
        is_processed=False
    )
    
    logger.info(f"Nombre de documents Word à analyser: {word_documents.count()}")
    
    results = []
    processed_count = 0
    error_count = 0
    
    for doc in word_documents:
        logger.info(f"Traitement de: {doc.filename}")
        
        # Vérifier que le fichier existe
        if not os.path.exists(doc.file_path):
            logger.warning(f"Fichier non trouvé: {doc.file_path}")
            continue
        
        # Extraire le texte
        content = extract_text_from_docx(doc.file_path)
        if not content:
            logger.warning(f"Impossible d'extraire le texte de: {doc.filename}")
            error_count += 1
            continue
        
        # Analyser avec OpenAI
        analysis = analyze_with_openai(content, doc.filename)
        
        # Mettre à jour le document dans la base
        try:
            doc.content = content[:5000]  # Limiter la taille stockée
            doc.content_length = len(content)
            doc.language = analysis.get('langue', 'Non déterminé')
            doc.theme = analysis.get('theme', 'Non déterminé')
            doc.confidence = analysis.get('confiance', 'Moyen')
            doc.is_processed = True
            doc.extraction_success = True
            doc.analysis_success = True
            doc.processed_at = datetime.now()
            doc.save()
            
            processed_count += 1
            logger.info(f"✅ {doc.filename} - Langue: {doc.language}, Thème: {doc.theme}")
            
            # Ajouter aux résultats
            results.append({
                'filename': doc.filename,
                'langue': doc.language,
                'theme': doc.theme,
                'confiance': doc.confidence,
                'taille_contenu': len(content),
                'date_traitement': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {doc.filename}: {e}")
            error_count += 1
    
    # Sauvegarder les résultats dans le fichier result
    result_data = {
        'date_execution': datetime.now().isoformat(),
        'total_documents': len(results),
        'documents_traites': processed_count,
        'erreurs': error_count,
        'documents': results
    }
    
    result_file = 'result.json'
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Résultats sauvegardés dans {result_file}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier result: {e}")
    
    # Résumé final
    logger.info("=== RÉSUMÉ FINAL ===")
    logger.info(f"Documents traités avec succès: {processed_count}")
    logger.info(f"Erreurs: {error_count}")
    logger.info(f"Fichier de résultats: {result_file}")
    
    print(f"\n✅ Analyse terminée!")
    print(f"📊 {processed_count} documents traités avec succès")
    print(f"❌ {error_count} erreurs")
    print(f"📄 Résultats sauvegardés dans: {result_file}")

if __name__ == '__main__':
    main()