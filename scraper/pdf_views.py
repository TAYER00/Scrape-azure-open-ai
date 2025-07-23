import os
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import Http404, HttpResponse, FileResponse
from django.urls import reverse
from django.contrib import messages
import mimetypes
from pathlib import Path

def get_pdf_files_from_media(subdirectory=''):
    """
    Récupère tous les fichiers PDF du dossier media/pdf_downloads/
    
    Args:
        subdirectory (str): Sous-dossier optionnel dans pdf_downloads
    
    Returns:
        list: Liste des fichiers PDF avec leurs métadonnées
    """
    pdf_files = []
    
    # Construire le chemin vers le dossier PDF
    if subdirectory:
        pdf_directory = os.path.join(settings.MEDIA_ROOT, 'pdf_downloads', subdirectory)
    else:
        pdf_directory = os.path.join(settings.MEDIA_ROOT, 'pdf_downloads')
    
    # Vérifier si le dossier existe
    if not os.path.exists(pdf_directory):
        return pdf_files
    
    try:
        # Parcourir tous les fichiers du dossier
        for filename in os.listdir(pdf_directory):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(pdf_directory, filename)
                
                # Obtenir les informations du fichier
                file_stats = os.stat(file_path)
                file_size = file_stats.st_size
                
                # Créer le titre à partir du nom de fichier
                title = os.path.splitext(filename)[0]
                title = title.replace('-', ' ').replace('_', ' ').title()
                
                # Construire le chemin relatif pour l'URL
                if subdirectory:
                    relative_path = f'{subdirectory}/{filename}'
                else:
                    relative_path = filename
                
                pdf_files.append({
                    'title': title,
                    'filename': relative_path,
                    'original_filename': filename,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'date': None  # Peut être ajouté plus tard si nécessaire
                })
    
    except OSError as e:
        print(f"Erreur lors de la lecture du dossier {pdf_directory}: {e}")
    
    # Trier par titre
    return sorted(pdf_files, key=lambda x: x['title'])

def pdf_list_view(request, category=None):
    """
    Vue pour afficher la liste des PDFs
    
    Args:
        request: Requête HTTP
        category (str): Catégorie optionnelle de PDFs
    
    Returns:
        HttpResponse: Page avec la liste des PDFs
    """
    # Récupérer les fichiers PDF
    pdf_files = get_pdf_files_from_media(category)
    
    # Définir le titre de la page selon la catégorie
    if category:
        page_title = f"Documents PDF - {category.title()}"
    else:
        page_title = "Documents PDF"
    
    context = {
        'pdf_files': pdf_files,
        'page_title': page_title,
        'category': category,
        'total_files': len(pdf_files)
    }
    
    return render(request, 'scraper/pdf_list.html', context)

def pdf_viewer_view(request, filename):
    """
    Vue pour afficher un PDF spécifique
    
    Args:
        request: Requête HTTP
        filename (str): Nom du fichier PDF
    
    Returns:
        HttpResponse: Page de visualisation du PDF
    """
    # Construire le chemin complet du fichier
    file_path = os.path.join(settings.MEDIA_ROOT, 'pdf_downloads', filename)
    
    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        raise Http404("Le fichier PDF demandé n'existe pas.")
    
    # Créer le titre à partir du nom de fichier
    pdf_title = os.path.splitext(filename)[0]
    pdf_title = pdf_title.replace('-', ' ').replace('_', ' ').title()
    
    context = {
        'pdf_title': pdf_title,
        'pdf_filename': filename,
        'file_exists': True
    }
    
    return render(request, 'scraper/pdf_viewer.html', context)

def serve_pdf(request, filename):
    """
    Vue pour servir directement un fichier PDF
    
    Args:
        request: Requête HTTP
        filename (str): Nom du fichier PDF
    
    Returns:
        FileResponse: Fichier PDF
    """
    # Construire le chemin complet du fichier
    file_path = os.path.join(settings.MEDIA_ROOT, 'pdf_downloads', filename)
    
    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        raise Http404("Le fichier PDF demandé n'existe pas.")
    
    # Déterminer le type MIME
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/pdf'
    
    # Retourner le fichier
    try:
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            filename=filename
        )
        return response
    except IOError:
        raise Http404("Erreur lors de la lecture du fichier PDF.")

def pdf_download_view(request, filename):
    """
    Vue pour forcer le téléchargement d'un PDF
    
    Args:
        request: Requête HTTP
        filename (str): Nom du fichier PDF
    
    Returns:
        FileResponse: Fichier PDF avec en-têtes de téléchargement
    """
    # Construire le chemin complet du fichier
    file_path = os.path.join(settings.MEDIA_ROOT, 'pdf_downloads', filename)
    
    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        raise Http404("Le fichier PDF demandé n'existe pas.")
    
    try:
        # Créer la réponse avec en-têtes de téléchargement
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=filename
        )
        
        # Ajouter des en-têtes supplémentaires
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except IOError:
        raise Http404("Erreur lors de la lecture du fichier PDF.")

def create_media_pdf_directory():
    """
    Crée le dossier media/pdf_downloads/ s'il n'existe pas
    """
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_downloads')
    os.makedirs(pdf_dir, exist_ok=True)
    return pdf_dir

def copy_pdfs_to_media(source_directories):
    """
    Copie les PDFs des dossiers sources vers media/pdf_downloads/
    
    Args:
        source_directories (list): Liste des dossiers sources contenant des PDFs
    """
    import shutil
    
    # Créer le dossier de destination
    dest_dir = create_media_pdf_directory()
    
    copied_files = []
    
    for source_dir in source_directories:
        if os.path.exists(source_dir):
            for filename in os.listdir(source_dir):
                if filename.lower().endswith('.pdf'):
                    source_file = os.path.join(source_dir, filename)
                    dest_file = os.path.join(dest_dir, filename)
                    
                    # Éviter d'écraser les fichiers existants
                    if not os.path.exists(dest_file):
                        try:
                            shutil.copy2(source_file, dest_file)
                            copied_files.append(filename)
                        except Exception as e:
                            print(f"Erreur lors de la copie de {filename}: {e}")
    
    return copied_files

# Vue d'exemple pour tester le système
def pdf_demo_view(request):
    """
    Vue de démonstration pour tester l'affichage des PDFs
    """
    # Créer quelques exemples de PDFs pour la démonstration
    demo_pdfs = [
        {
            'title': 'Document Exemple 1',
            'filename': 'exemple1.pdf',
            'original_filename': 'exemple1.pdf',
            'size': 1024000,
            'size_mb': 1.0,
            'date': '2024-01-15'
        },
        {
            'title': 'Rapport Annuel 2023',
            'filename': 'rapport-annuel-2023.pdf',
            'original_filename': 'rapport-annuel-2023.pdf',
            'size': 2048000,
            'size_mb': 2.0,
            'date': '2023-12-31'
        }
    ]
    
    context = {
        'pdf_files': demo_pdfs,
        'page_title': 'Démonstration - Documents PDF',
        'category': 'demo',
        'total_files': len(demo_pdfs)
    }
    
    return render(request, 'scraper/pdf_list.html', context)