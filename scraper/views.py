import os
import json
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

def get_pdf_files(directory):
    """Récupère tous les fichiers PDF d'un répertoire avec leurs métadonnées."""
    pdf_files = []
    if os.path.exists(directory):
        # Pour BKAM, vérifier le sous-dossier pdf_scraper
        if 'bkam.ma' in directory:
            directory = os.path.join(directory, 'pdf_scraper')
            if not os.path.exists(directory):
                return pdf_files

        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                file_path = os.path.join(directory, filename)
                title = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ')
                
                # Générer le bon chemin d'URL pour les PDFs
                if 'bkam.ma' in directory:
                    # Pour BKAM: /bkam.ma/bkam.ma/pdf_downloads/[Communiques|Discours]/pdf_scraper/filename.pdf
                    category = os.path.basename(os.path.dirname(directory))  # Communiques ou Discours
                    file_url = f'/bkam.ma/bkam.ma/pdf_downloads/{category}/pdf_scraper/{filename}'
                elif 'agriculture.gov.ma' in directory:
                    # Pour Agriculture: /agriculture.gov.ma/pdf_downloads/filename.pdf
                    file_url = f'/agriculture.gov.ma/pdf_downloads/{filename}'
                elif 'cese.ma' in directory:
                    # Pour CESE: /cese.ma/pdf_downloads/filename.pdf
                    file_url = f'/cese.ma/pdf_downloads/{filename}'
                elif 'finances.gov.ma' in directory:
                    # Pour Finances: /finances.gov.ma/pdf_downloads/filename.pdf
                    file_url = f'/finances.gov.ma/pdf_downloads/{filename}'
                elif 'oecd.org' in directory:
                    # Pour OECD: /oecd.org/pdf_downloads/filename.pdf
                    file_url = f'/oecd.org/pdf_downloads/{filename}'
                else:
                    # Fallback pour les autres sites
                    site_name = os.path.basename(os.path.dirname(directory))
                    file_url = f'/{site_name}/pdf_downloads/{filename}'
                
                pdf_files.append({
                    'title': title,
                    'file_path': file_url,
                    'date': None
                })
    return sorted(pdf_files, key=lambda x: x['title'])

def get_word_files(directory):
    """Récupère tous les fichiers Word d'un répertoire avec leurs métadonnées."""
    word_files = []
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith('.docx'):
                file_path = os.path.join(directory, filename)
                title = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ')
                
                # Générer le bon chemin d'URL pour les fichiers Word
                if 'finances.gov.ma' in directory:
                    # Pour Finances: /finances.gov.ma/words_downloads/filename.docx
                    file_url = f'/finances.gov.ma/words_downloads/{filename}'
                elif 'oecd.org' in directory:
                    # Pour OECD: /oecd.org/words_downloads/filename.docx
                    file_url = f'/oecd.org/words_downloads/{filename}'
                else:
                    # Fallback pour les autres sites
                    site_name = os.path.basename(os.path.dirname(directory))
                    file_url = f'/{site_name}/words_downloads/{filename}'
                
                word_files.append({
                    'title': title,
                    'file_path': file_url,
                    'date': None
                })
    return sorted(word_files, key=lambda x: x['title'])

def home(request):
    return render(request, 'scraper/home.html')

def bkam_communiques(request):
    documents = get_pdf_files('bkam.ma/bkam.ma/pdf_downloads/Communiques')
    context = {
        'site_name': 'BKAM',
        'site_icon': 'fas fa-bullhorn',
        'page_title': 'Communiqués de Bank Al-Maghrib',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def download_word_file(request, site, filename):
    """Vue pour télécharger les fichiers Word."""
    if site == 'finances.gov.ma':
        file_path = os.path.join('C:\\Users\\anouar\\Downloads\\Scraping-web-sites-auto-naviguation\\Scraping-web-sites-auto-naviguation-master\\finances.gov.ma\\words_downloads', filename)
    elif site == 'oecd.org':
        file_path = os.path.join('C:\\Users\\anouar\\Downloads\\Scraping-web-sites-auto-naviguation\\Scraping-web-sites-auto-naviguation-master\\oecd.org\\words_downloads', filename)
    else:
        raise Http404("Site non trouvé")
    
    if not os.path.exists(file_path):
        raise Http404("Fichier non trouvé")
    
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

def bkam_discours(request):
    documents = get_pdf_files('bkam.ma/bkam.ma/pdf_downloads/Discours')
    context = {
        'site_name': 'BKAM',
        'site_icon': 'fas fa-microphone',
        'page_title': 'Discours de Bank Al-Maghrib',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def agriculture_documents(request):
    documents = get_pdf_files('agriculture.gov.ma/pdf_downloads')
    context = {
        'site_name': 'Agriculture.gov.ma',
        'site_icon': 'fas fa-leaf',
        'page_title': 'Documents du Ministère de l\'Agriculture',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def cese_documents(request):
    documents = get_pdf_files('cese.ma/pdf_downloads')
    context = {
        'site_name': 'CESE.ma',
        'site_icon': 'fas fa-landmark',
        'page_title': 'Documents du CESE',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def finances_documents(request):
    word_documents = get_word_files('C:\\Users\\anouar\\Downloads\\Scraping-web-sites-auto-naviguation\\Scraping-web-sites-auto-naviguation-master\\finances.gov.ma\\words_downloads')
    context = {
        'site_name': 'Finances.gov.ma',
        'site_icon': 'fas fa-coins',
        'page_title': 'Documents du Ministère des Finances',
        'documents': word_documents
    }
    return render(request, 'scraper/documents.html', context)

def oecd_documents(request):
    word_documents = get_word_files('C:\\Users\\anouar\\Downloads\\Scraping-web-sites-auto-naviguation\\Scraping-web-sites-auto-naviguation-master\\oecd.org\\words_downloads')
    context = {
        'site_name': 'OECD.org',
        'site_icon': 'fas fa-globe',
        'page_title': 'Documents de l\'OCDE',
        'documents': word_documents
    }
    return render(request, 'scraper/documents.html', context)

# Nouvelles vues pour l'analyse PDF
def pdf_analysis_view(request):
    """
    Vue principale pour afficher l'interface d'analyse des PDFs
    """
    return render(request, 'scraper/pdf_analysis.html')

@require_GET
def pdf_analysis_api(request):
    """
    API pour récupérer les données d'analyse des PDFs au format JSON
    """
    try:
        # Chemin vers le fichier JSON
        json_file_path = os.path.join(
            settings.BASE_DIR, 
            'scraper', 
            'static', 
            'data', 
            'pdf_analysis_results.json'
        )
        
        # Vérifier si le fichier existe
        if not os.path.exists(json_file_path):
            return JsonResponse({
                'error': 'Fichier de données non trouvé',
                'message': 'Le fichier scraper/static/data/pdf_analysis_results.json n\'existe pas.'
            }, status=404)
        
        # Lire et retourner les données JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return JsonResponse(data, safe=False)
        
    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': 'Erreur de format JSON',
            'message': f'Le fichier JSON est mal formaté: {str(e)}'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Erreur serveur',
            'message': f'Une erreur inattendue s\'est produite: {str(e)}'
        }, status=500)
