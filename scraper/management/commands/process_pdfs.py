import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from scraper.models import PDFDocument
from utils.pdf_tools import (
    scan_default_directories,
    extract_text_from_local_pdf,
    get_pdf_metadata
)
from utils.openai_client import OpenAIAnalyzer
from django.utils import timezone

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Traite les PDFs locaux : extraction de texte et analyse avec Azure OpenAI'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            help='Répertoire spécifique à traiter (optionnel)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Fichier PDF spécifique à traiter (optionnel)'
        )
        parser.add_argument(
            '--max-files',
            type=int,
            default=50,
            help='Nombre maximum de fichiers à traiter (défaut: 50)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Retraiter les PDFs déjà traités'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans traitement réel'
        )
        parser.add_argument(
            '--skip-analysis',
            action='store_true',
            help='Extraire seulement le texte, sans analyse OpenAI'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Début du traitement des PDFs...')
        )
        
        # Initialiser l'analyseur OpenAI si nécessaire
        analyzer = None
        if not options['skip_analysis']:
            try:
                analyzer = OpenAIAnalyzer()
                self.stdout.write(
                    self.style.SUCCESS('✅ Client Azure OpenAI initialisé')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur initialisation OpenAI: {e}')
                )
                if not options['dry_run']:
                    raise CommandError(f'Impossible d\'initialiser Azure OpenAI: {e}')
        
        # Déterminer les fichiers à traiter
        pdf_files = self._get_pdf_files(options)
        
        if not pdf_files:
            self.stdout.write(
                self.style.WARNING('⚠️ Aucun fichier PDF trouvé')
            )
            return
        
        # Limiter le nombre de fichiers
        max_files = options['max_files']
        if len(pdf_files) > max_files:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ {len(pdf_files)} fichiers trouvés, limitation à {max_files}'
                )
            )
            pdf_files = pdf_files[:max_files]
        
        self.stdout.write(
            self.style.SUCCESS(f'📁 {len(pdf_files)} fichiers à traiter')
        )
        
        # Traiter chaque fichier
        processed_count = 0
        error_count = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            self.stdout.write(f'\n📄 [{i}/{len(pdf_files)}] {pdf_file["filename"]}')
            
            try:
                if options['dry_run']:
                    self.stdout.write('   🔍 Mode simulation - fichier non traité')
                    continue
                
                success = self._process_single_pdf(
                    pdf_file, 
                    analyzer, 
                    options['force'],
                    options['skip_analysis']
                )
                
                if success:
                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Traité avec succès')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR('   ❌ Échec du traitement')
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Erreur: {str(e)}')
                )
                logger.error(f'Erreur traitement {pdf_file["filename"]}: {e}')
        
        # Résumé final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Traitement terminé:\n'
                f'   ✅ Succès: {processed_count}\n'
                f'   ❌ Erreurs: {error_count}\n'
                f'   📊 Total: {len(pdf_files)}'
            )
        )
    
    def _get_pdf_files(self, options):
        """Récupère la liste des fichiers PDF à traiter."""
        pdf_files = []
        
        if options['file']:
            # Traiter un fichier spécifique
            file_path = options['file']
            if not os.path.exists(file_path):
                raise CommandError(f'Fichier non trouvé: {file_path}')
            
            if not file_path.lower().endswith('.pdf'):
                raise CommandError(f'Le fichier doit être un PDF: {file_path}')
            
            pdf_files = [{
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'source_directory': os.path.dirname(file_path)
            }]
            
        elif options['directory']:
            # Traiter un répertoire spécifique
            directory = options['directory']
            if not os.path.exists(directory):
                raise CommandError(f'Répertoire non trouvé: {directory}')
            
            pdf_files = self._scan_directory(directory)
            
        else:
            # Traiter les répertoires par défaut
            pdf_files = scan_default_directories()
        
        # Filtrer les fichiers déjà traités si nécessaire
        if not options['force']:
            pdf_files = self._filter_unprocessed_files(pdf_files)
        
        return pdf_files
    
    def _scan_directory(self, directory):
        """Scanne un répertoire pour trouver les PDFs."""
        pdf_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    pdf_files.append({
                        'filename': file,
                        'file_path': file_path,
                        'source_directory': root
                    })
        
        return pdf_files
    
    def _filter_unprocessed_files(self, pdf_files):
        """Filtre les fichiers déjà traités."""
        processed_files = set(
            PDFDocument.objects.filter(is_processed=True)
            .values_list('file_path', flat=True)
        )
        
        return [
            pdf for pdf in pdf_files 
            if pdf['file_path'] not in processed_files
        ]
    
    def _process_single_pdf(self, pdf_file, analyzer, force=False, skip_analysis=False):
        """Traite un seul fichier PDF."""
        file_path = pdf_file['file_path']
        filename = pdf_file['filename']
        source_directory = pdf_file.get('source_directory', pdf_file.get('directory', ''))
        
        # Vérifier si le fichier existe déjà en base
        pdf_doc, created = PDFDocument.objects.get_or_create(
            file_path=file_path,
            defaults={
                'filename': filename,
                'source_directory': source_directory
            }
        )
        
        # Si déjà traité et pas de force, passer
        if not created and pdf_doc.is_processed and not force:
            self.stdout.write('   ⏭️ Déjà traité (utilisez --force pour retraiter)')
            return True
        
        try:
            # 1. Extraction du texte
            self.stdout.write('   📖 Extraction du texte...')
            extracted_text = extract_text_from_local_pdf(file_path)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                pdf_doc.mark_as_processed(
                    success=False, 
                    error_message="Texte extrait vide ou trop court"
                )
                return False
            
            # 2. Métadonnées du fichier
            metadata = get_pdf_metadata(file_path)
            
            # 3. Mise à jour des informations de base
            pdf_doc.content = extracted_text
            pdf_doc.content_length = len(extracted_text)
            pdf_doc.extraction_success = True
            pdf_doc.page_count = metadata.get('page_count', 0)
            pdf_doc.file_size = metadata.get('file_size', 0)
            
            # 4. Analyse avec OpenAI (si activée)
            if not skip_analysis and analyzer:
                self.stdout.write('   🤖 Analyse avec Azure OpenAI...')
                
                try:
                    analysis_result = analyzer.analyze_pdf_content(extracted_text)
                    
                    pdf_doc.language = analysis_result.get('language', 'Inconnu')
                    pdf_doc.theme = analysis_result.get('theme', 'Inconnu')
                    pdf_doc.confidence = analysis_result.get('confidence', 'Moyen')
                    pdf_doc.analysis_success = True
                    
                    # Générer un résumé si possible
                    if len(extracted_text) > 100:
                        summary = analyzer.get_summary(extracted_text)
                        pdf_doc.summary = summary
                    
                except Exception as e:
                    logger.error(f'Erreur analyse OpenAI pour {filename}: {e}')
                    pdf_doc.analysis_success = False
                    pdf_doc.error_message = f'Erreur analyse OpenAI: {str(e)}'
            else:
                pdf_doc.analysis_success = True  # Pas d'analyse demandée
            
            # 5. Marquer comme traité
            pdf_doc.is_processed = True
            pdf_doc.processed_at = timezone.now()
            pdf_doc.save()
            
            return True
            
        except Exception as e:
            logger.error(f'Erreur traitement {filename}: {e}')
            pdf_doc.mark_as_processed(
                success=False,
                error_message=str(e)
            )
            return False
    
    def _format_file_size(self, size_bytes):
        """Formate la taille de fichier en unités lisibles."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"