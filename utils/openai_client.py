import os
import logging
from typing import Dict, Optional, Tuple
from openai import AzureOpenAI
from django.conf import settings
import json
import re

# Configuration du logging
logger = logging.getLogger(__name__)

class OpenAIAnalyzer:
    """
    Client pour analyser le contenu des PDFs avec Azure OpenAI.
    """
    
    def __init__(self):
        """
        Initialise le client Azure OpenAI avec les paramètres de configuration.
        """
        try:
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version="2024-02-01",
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
            logger.info("Client Azure OpenAI initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Azure OpenAI: {str(e)}")
            raise
    
    def analyze_pdf_content(self, text: str, max_chars: int = 3000) -> Dict[str, str]:
        """
        Analyse le contenu d'un PDF pour détecter la langue et la thématique.
        
        Args:
            text (str): Texte extrait du PDF
            max_chars (int): Nombre maximum de caractères à analyser
            
        Returns:
            Dict[str, str]: Dictionnaire contenant la langue et la thématique
        """
        if not text or not text.strip():
            return {
                'language': 'Inconnu',
                'theme': 'Inconnu',
                'confidence': 'Faible',
                'error': 'Texte vide ou invalide'
            }
        
        # Limiter la taille du texte pour l'analyse
        analysis_text = text[:max_chars] if len(text) > max_chars else text
        
        prompt = f"""
        Analyse le texte suivant extrait d'un document PDF :
        
        {analysis_text}
        
        Donne-moi uniquement :
        1. La langue principale du document (français, anglais, arabe, etc.)
        2. La thématique générale du document (économie, finance, politique, juridique, etc.)
        3. Un niveau de confiance (Élevé, Moyen, Faible)
        
        Réponds EXACTEMENT dans ce format JSON :
        {{
            "language": "langue détectée",
            "theme": "thématique principale",
            "confidence": "niveau de confiance"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "Tu es un assistant intelligent spécialisé dans l'analyse de documents. Tu réponds toujours en JSON valide."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"Réponse brute d'OpenAI: {result_text}")
            
            # Tenter de parser le JSON
            try:
                result = json.loads(result_text)
                return {
                    'language': result.get('language', 'Inconnu'),
                    'theme': result.get('theme', 'Inconnu'),
                    'confidence': result.get('confidence', 'Moyen'),
                    'raw_response': result_text
                }
            except json.JSONDecodeError:
                # Fallback: parser manuellement si le JSON est invalide
                return self._parse_fallback_response(result_text)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avec OpenAI: {str(e)}")
            return {
                'language': 'Erreur',
                'theme': 'Erreur',
                'confidence': 'Faible',
                'error': str(e)
            }
    
    def _parse_fallback_response(self, text: str) -> Dict[str, str]:
        """
        Parse la réponse d'OpenAI en cas d'échec du parsing JSON.
        
        Args:
            text (str): Texte de réponse brut
            
        Returns:
            Dict[str, str]: Résultat parsé
        """
        result = {
            'language': 'Inconnu',
            'theme': 'Inconnu', 
            'confidence': 'Faible',
            'raw_response': text
        }
        
        # Rechercher les patterns dans le texte
        language_match = re.search(r'langue[^:]*:?\s*([^\n,]+)', text, re.IGNORECASE)
        theme_match = re.search(r'th[eé]matique[^:]*:?\s*([^\n,]+)', text, re.IGNORECASE)
        confidence_match = re.search(r'confiance[^:]*:?\s*([^\n,]+)', text, re.IGNORECASE)
        
        if language_match:
            result['language'] = language_match.group(1).strip()
        if theme_match:
            result['theme'] = theme_match.group(1).strip()
        if confidence_match:
            result['confidence'] = confidence_match.group(1).strip()
            
        return result
    
    def analyze_multiple_pdfs(self, pdf_data_list: list) -> list:
        """
        Analyse plusieurs PDFs en lot.
        
        Args:
            pdf_data_list (list): Liste des données PDF avec texte extrait
            
        Returns:
            list: Liste des résultats d'analyse
        """
        results = []
        
        for i, pdf_data in enumerate(pdf_data_list):
            logger.info(f"Analyse du PDF {i+1}/{len(pdf_data_list)}: {pdf_data.get('filename', 'Inconnu')}")
            
            if 'extracted_text' in pdf_data and pdf_data['extraction_success']:
                analysis = self.analyze_pdf_content(pdf_data['extracted_text'])
                pdf_data.update(analysis)
            else:
                pdf_data.update({
                    'language': 'Erreur extraction',
                    'theme': 'Erreur extraction',
                    'confidence': 'Faible'
                })
            
            results.append(pdf_data)
        
        return results
    
    def get_summary(self, text: str, max_chars: int = 2000) -> str:
        """
        Génère un résumé du contenu du PDF.
        
        Args:
            text (str): Texte du PDF
            max_chars (int): Nombre maximum de caractères à analyser
            
        Returns:
            str: Résumé du contenu
        """
        if not text or not text.strip():
            return "Impossible de générer un résumé : texte vide"
        
        analysis_text = text[:max_chars] if len(text) > max_chars else text
        
        prompt = f"""
        Génère un résumé concis (maximum 200 mots) du document suivant :
        
        {analysis_text}
        
        Le résumé doit être en français et capturer les points clés du document.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un assistant qui génère des résumés clairs et concis de documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {str(e)}")
            return f"Erreur lors de la génération du résumé: {str(e)}"

# Fonctions utilitaires pour compatibilité
def analyze_pdf_content(text: str) -> str:
    """
    Fonction de compatibilité pour analyser le contenu d'un PDF.
    
    Args:
        text (str): Texte extrait du PDF
        
    Returns:
        str: Résultat de l'analyse au format texte
    """
    analyzer = OpenAIAnalyzer()
    result = analyzer.analyze_pdf_content(text)
    
    return f"""Langue : {result['language']}
Thématique : {result['theme']}
Confiance : {result['confidence']}"""

def detect_language_and_theme(text: str) -> Tuple[str, str]:
    """
    Détecte la langue et la thématique d'un texte.
    
    Args:
        text (str): Texte à analyser
        
    Returns:
        Tuple[str, str]: (langue, thématique)
    """
    analyzer = OpenAIAnalyzer()
    result = analyzer.analyze_pdf_content(text)
    
    return result['language'], result['theme']

if __name__ == "__main__":
    # Test du client
    try:
        analyzer = OpenAIAnalyzer()
        test_text = "Ceci est un document de test en français sur l'économie marocaine."
        result = analyzer.analyze_pdf_content(test_text)
        print(f"Résultat du test: {result}")
    except Exception as e:
        print(f"Erreur lors du test: {e}")