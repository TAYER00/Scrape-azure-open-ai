#!/usr/bin/env python
import os
import django
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_scraper.settings')
django.setup()

from scraper.models import PDFDocument
from django.utils import timezone
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_word_documents_to_db():
    """
    Ajoute tous les documents Word des répertoires words_downloads à la base de données.
    """
    # Répertoires à scanner
    directories = [
        'agriculture.gov.ma/words_downloads',
        'cese.ma/words_downloads', 
        'finances.gov.ma/words_downloads',
        'oecd.org/words_downloads'
    ]
    
    total_added = 0
    total_existing = 0
    
    for directory in directories:
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.warning(f"Répertoire non trouvé: {directory}")
            continue
            
        logger.info(f"Scanning répertoire: {directory}")
        
        # Scanner tous les fichiers .docx
        for file_path in dir_path.glob('*.docx'):
            filename = file_path.name
            full_path = str(file_path.absolute())
            
            # Vérifier si le document existe déjà
            existing_doc = PDFDocument.objects.filter(
                filename=filename,
                file_path=full_path
            ).first()
            
            if existing_doc:
                logger.info(f"Document déjà existant: {filename}")
                total_existing += 1
                continue
            
            # Créer un nouveau document
            try:
                # Obtenir la taille du fichier
                file_size = file_path.stat().st_size
                
                pdf_doc = PDFDocument.objects.create(
                    filename=filename,
                    file_path=full_path,
                    file_size=file_size,
                    is_processed=False,  # Les documents Word ne sont pas traités par défaut
                    extraction_success=False,
                    analysis_success=False,
                    content="",  # Contenu vide pour les documents Word
                    content_length=0,
                    language=None,
                    theme=None,
                    confidence="Moyen",
                    summary="",
                    error_message=None,
                    is_retained=True,  # Marquer comme conservé par défaut
                    source_directory=directory,
                    page_count=0
                )
                
                logger.info(f"Document ajouté: {filename}")
                total_added += 1
                
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout de {filename}: {str(e)}")
    
    # Résumé
    logger.info(f"\n=== RÉSUMÉ ===")
    logger.info(f"Documents ajoutés: {total_added}")
    logger.info(f"Documents déjà existants: {total_existing}")
    logger.info(f"Total traité: {total_added + total_existing}")
    
    return total_added, total_existing

if __name__ == '__main__':
    print("🚀 Ajout des documents Word à la base de données...")
    added, existing = add_word_documents_to_db()
    print(f"\n✅ Terminé! {added} documents ajoutés, {existing} déjà existants.")