# Package utils pour les outils utilitaires du projet

__version__ = '1.0.0'
__author__ = 'Assistant IA'

# Imports des modules principaux
from .pdf_tools import (
    extract_text_from_local_pdf,
    get_pdf_files_from_directories,
    extract_text_from_pdf_batch,
    scan_default_directories,
    clean_extracted_text,
    get_pdf_metadata
)

try:
    from .openai_client import (
        analyze_pdf_content,
        detect_language_and_theme,
        OpenAIAnalyzer
    )
except ImportError:
    # Le module openai_client n'est pas encore créé
    pass

__all__ = [
    'extract_text_from_local_pdf',
    'get_pdf_files_from_directories', 
    'extract_text_from_pdf_batch',
    'scan_default_directories',
    'clean_extracted_text',
    'get_pdf_metadata',
    'analyze_pdf_content',
    'detect_language_and_theme',
    'OpenAIAnalyzer'
]