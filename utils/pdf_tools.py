import os
import fitz  # PyMuPDF
from pathlib import Path
import logging
from typing import List, Dict, Optional

# Configuration du logging
logger = logging.getLogger(__name__)

def extract_text_from_local_pdf(file_path: str) -> str:
    """
    Extrait le texte d'un fichier PDF local.
    
    Args:
        file_path (str): Chemin vers le fichier PDF local
        
    Returns:
        str: Texte extrait du PDF
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        Exception: Si l'extraction échoue
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier PDF n'existe pas : {file_path}")
    
    try:
        doc = fitz.open(file_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            text += "\n"  # Ajouter un saut de ligne entre les pages
        
        doc.close()
        
        # Nettoyer le texte
        text = clean_extracted_text(text)
        
        logger.info(f"Texte extrait avec succès de {file_path} ({len(text)} caractères)")
        return text
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte de {file_path}: {str(e)}")
        raise Exception(f"Impossible d'extraire le texte du PDF : {str(e)}")

def clean_extracted_text(text: str) -> str:
    """
    Nettoie le texte extrait en supprimant les caractères indésirables.
    
    Args:
        text (str): Texte brut extrait
        
    Returns:
        str: Texte nettoyé
    """
    # Supprimer les caractères de contrôle et les espaces multiples
    import re
    
    # Remplacer les sauts de ligne multiples par un seul
    text = re.sub(r'\n+', '\n', text)
    
    # Remplacer les espaces multiples par un seul
    text = re.sub(r' +', ' ', text)
    
    # Supprimer les espaces en début et fin de ligne
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Supprimer les lignes vides
    text = '\n'.join([line for line in text.split('\n') if line.strip()])
    
    return text.strip()

def get_pdf_files_from_directories(directories: List[str]) -> List[Dict[str, str]]:
    """
    Récupère tous les fichiers PDF des répertoires spécifiés.
    
    Args:
        directories (List[str]): Liste des répertoires à scanner
        
    Returns:
        List[Dict[str, str]]: Liste des fichiers PDF avec leurs métadonnées
    """
    pdf_files = []
    
    for directory in directories:
        if not os.path.exists(directory):
            logger.warning(f"Le répertoire n'existe pas : {directory}")
            continue
            
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        
                        pdf_info = {
                            'file_path': file_path,
                            'filename': file,
                            'directory': directory,
                            'relative_path': os.path.relpath(file_path, directory),
                            'size_bytes': file_size,
                            'size_mb': round(file_size / (1024 * 1024), 2)
                        }
                        
                        pdf_files.append(pdf_info)
                        
        except Exception as e:
            logger.error(f"Erreur lors du scan du répertoire {directory}: {str(e)}")
    
    logger.info(f"Trouvé {len(pdf_files)} fichiers PDF dans {len(directories)} répertoires")
    return pdf_files

def extract_text_from_pdf_batch(pdf_files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Extrait le texte de plusieurs fichiers PDF en lot.
    
    Args:
        pdf_files (List[Dict[str, str]]): Liste des fichiers PDF
        
    Returns:
        List[Dict[str, str]]: Liste des fichiers avec le texte extrait
    """
    results = []
    
    for pdf_info in pdf_files:
        try:
            text = extract_text_from_local_pdf(pdf_info['file_path'])
            pdf_info['extracted_text'] = text
            pdf_info['extraction_success'] = True
            pdf_info['text_length'] = len(text)
            
        except Exception as e:
            pdf_info['extracted_text'] = ""
            pdf_info['extraction_success'] = False
            pdf_info['extraction_error'] = str(e)
            pdf_info['text_length'] = 0
            logger.error(f"Échec de l'extraction pour {pdf_info['filename']}: {str(e)}")
        
        results.append(pdf_info)
    
    successful_extractions = sum(1 for r in results if r['extraction_success'])
    logger.info(f"Extraction terminée : {successful_extractions}/{len(results)} fichiers traités avec succès")
    
    return results

def get_pdf_metadata(file_path: str) -> Dict[str, str]:
    """
    Récupère les métadonnées d'un fichier PDF.
    
    Args:
        file_path (str): Chemin vers le fichier PDF
        
    Returns:
        Dict[str, str]: Métadonnées du PDF
    """
    try:
        doc = fitz.open(file_path)
        metadata = doc.metadata
        doc.close()
        
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', '')
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des métadonnées de {file_path}: {str(e)}")
        return {}

# Configuration des répertoires par défaut
DEFAULT_PDF_DIRECTORIES = [
    'bkam.ma/bkam.ma/pdf_downloads/Communiques/pdf_scraper',
    'bkam.ma/bkam.ma/pdf_downloads/Discours/pdf_scraper',
    'cese.ma/pdf_downloads',
    'finances.gov.ma/pdf_downloads',
    'oecd.org/pdf_downloads'
]

def scan_default_directories() -> List[Dict[str, str]]:
    """
    Scanne les répertoires par défaut pour trouver les fichiers PDF.
    
    Returns:
        List[Dict[str, str]]: Liste des fichiers PDF trouvés
    """
    return get_pdf_files_from_directories(DEFAULT_PDF_DIRECTORIES)

if __name__ == "__main__":
    # Test de la fonction
    print("Scan des répertoires par défaut...")
    pdf_files = scan_default_directories()
    print(f"Trouvé {len(pdf_files)} fichiers PDF")
    
    if pdf_files:
        print("\nPremiers fichiers trouvés :")
        for pdf in pdf_files[:5]:
            print(f"- {pdf['filename']} ({pdf['size_mb']} MB)")