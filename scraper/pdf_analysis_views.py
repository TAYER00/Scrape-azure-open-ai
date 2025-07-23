from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from .models import PDFDocument
from utils.pdf_tools import extract_text_from_local_pdf, get_pdf_metadata
from utils.openai_client import OpenAIAnalyzer
import os
import json
from django.conf import settings

class PDFDocumentListView(ListView):
    """
    Vue pour afficher la liste des documents PDF analysés.
    """
    model = PDFDocument
    template_name = 'scraper/pdf_documents_list.html'
    context_object_name = 'pdf_documents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PDFDocument.objects.all()
        
        # Filtrage par langue
        language = self.request.GET.get('language')
        if language:
            queryset = queryset.filter(language__icontains=language)
        
        # Filtrage par thématique
        theme = self.request.GET.get('theme')
        if theme:
            queryset = queryset.filter(theme__icontains=theme)
        
        # Filtrage par statut
        status = self.request.GET.get('status')
        if status == 'processed':
            queryset = queryset.filter(is_processed=True)
        elif status == 'unprocessed':
            queryset = queryset.filter(is_processed=False)
        elif status == 'errors':
            queryset = queryset.filter(is_processed=False, error_message__isnull=False)
        
        # Recherche textuelle
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(filename__icontains=search) |
                Q(content__icontains=search) |
                Q(theme__icontains=search) |
                Q(language__icontains=search)
            )
        
        # Tri
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['filename', '-filename', 'language', '-language', 
                       'theme', '-theme', 'created_at', '-created_at', 
                       'file_size', '-file_size']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['stats'] = {
            'total_documents': PDFDocument.objects.count(),
            'processed_documents': PDFDocument.objects.filter(is_processed=True).count(),
            'error_documents': PDFDocument.objects.filter(
                is_processed=False, error_message__isnull=False
            ).count(),
            'languages': PDFDocument.objects.values('language').annotate(
                count=Count('language')
            ).order_by('-count')[:10],
            'themes': PDFDocument.objects.values('theme').annotate(
                count=Count('theme')
            ).order_by('-count')[:10],
        }
        
        # Paramètres de filtrage actuels
        context['current_filters'] = {
            'language': self.request.GET.get('language', ''),
            'theme': self.request.GET.get('theme', ''),
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        }
        
        return context

class PDFDocumentDetailView(DetailView):
    """
    Vue pour afficher les détails d'un document PDF.
    """
    model = PDFDocument
    template_name = 'scraper/pdf_document_detail.html'
    context_object_name = 'pdf_document'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Documents similaires (même thématique ou langue)
        similar_docs = PDFDocument.objects.filter(
            Q(theme=self.object.theme) | Q(language=self.object.language)
        ).exclude(pk=self.object.pk)[:5]
        
        context['similar_documents'] = similar_docs
        
        return context

def pdf_dashboard(request):
    """
    Tableau de bord principal pour les PDFs analysés.
    """
    # Statistiques générales
    total_docs = PDFDocument.objects.count()
    processed_docs = PDFDocument.objects.filter(is_processed=True).count()
    error_docs = PDFDocument.objects.filter(
        is_processed=False, error_message__isnull=False
    ).count()
    
    # Documents récents
    recent_docs = PDFDocument.objects.order_by('-created_at')[:10]
    
    # Répartition par langue
    languages_stats = PDFDocument.objects.values('language').annotate(
        count=Count('language')
    ).order_by('-count')[:10]
    
    # Répartition par thématique
    themes_stats = PDFDocument.objects.values('theme').annotate(
        count=Count('theme')
    ).order_by('-count')[:10]
    
    # Répartition par répertoire source
    directories_stats = PDFDocument.objects.values('source_directory').annotate(
        count=Count('source_directory')
    ).order_by('-count')[:10]
    
    context = {
        'total_docs': total_docs,
        'processed_docs': processed_docs,
        'error_docs': error_docs,
        'processing_rate': round((processed_docs / total_docs * 100), 1) if total_docs > 0 else 0,
        'recent_docs': recent_docs,
        'languages_stats': languages_stats,
        'themes_stats': themes_stats,
        'directories_stats': directories_stats,
    }
    
    return render(request, 'scraper/pdf_dashboard.html', context)

@require_http_methods(["POST"])
def reprocess_pdf(request, pdf_id):
    """
    Retraite un PDF spécifique.
    """
    pdf_doc = get_object_or_404(PDFDocument, pk=pdf_id)
    
    try:
        # Réinitialiser les statuts
        pdf_doc.is_processed = False
        pdf_doc.extraction_success = False
        pdf_doc.analysis_success = False
        pdf_doc.error_message = None
        
        # Extraction du texte
        if os.path.exists(pdf_doc.file_path):
            extracted_text = extract_text_from_local_pdf(pdf_doc.file_path)
            
            if extracted_text and len(extracted_text.strip()) > 10:
                pdf_doc.content = extracted_text
                pdf_doc.content_length = len(extracted_text)
                pdf_doc.extraction_success = True
                
                # Métadonnées
                metadata = get_pdf_metadata(pdf_doc.file_path)
                pdf_doc.page_count = metadata.get('page_count', 0)
                pdf_doc.file_size = metadata.get('file_size', 0)
                
                # Analyse OpenAI
                try:
                    analyzer = OpenAIAnalyzer()
                    analysis_result = analyzer.analyze_pdf_content(extracted_text)
                    
                    pdf_doc.language = analysis_result.get('language', 'Inconnu')
                    pdf_doc.theme = analysis_result.get('theme', 'Inconnu')
                    pdf_doc.confidence = analysis_result.get('confidence', 'Moyen')
                    pdf_doc.analysis_success = True
                    
                    # Résumé
                    if len(extracted_text) > 100:
                        summary = analyzer.get_summary(extracted_text)
                        pdf_doc.summary = summary
                    
                except Exception as e:
                    pdf_doc.analysis_success = False
                    pdf_doc.error_message = f'Erreur analyse OpenAI: {str(e)}'
                
                pdf_doc.mark_as_processed(success=True)
                messages.success(request, f'PDF "{pdf_doc.filename}" retraité avec succès.')
                
            else:
                pdf_doc.mark_as_processed(
                    success=False, 
                    error_message="Texte extrait vide ou trop court"
                )
                messages.error(request, f'Échec extraction de texte pour "{pdf_doc.filename}".')
        else:
            pdf_doc.mark_as_processed(
                success=False,
                error_message="Fichier PDF non trouvé"
            )
            messages.error(request, f'Fichier non trouvé: "{pdf_doc.file_path}".')
            
    except Exception as e:
        pdf_doc.mark_as_processed(
            success=False,
            error_message=str(e)
        )
        messages.error(request, f'Erreur lors du retraitement: {str(e)}')
    
    return redirect('scraper:pdf_detail', pk=pdf_id)

@require_http_methods(["POST"])
def toggle_retained(request, pdf_id):
    """
    Bascule le statut 'retenu' d'un PDF.
    """
    pdf_doc = get_object_or_404(PDFDocument, pk=pdf_id)
    pdf_doc.is_retained = not pdf_doc.is_retained
    pdf_doc.save()
    
    status = "marqué comme important" if pdf_doc.is_retained else "retiré des importants"
    messages.success(request, f'PDF "{pdf_doc.filename}" {status}.')
    
    return redirect('scraper:pdf_detail', pk=pdf_id)

def pdf_stats_api(request):
    """
    API pour récupérer les statistiques des PDFs (pour graphiques).
    """
    # Répartition par langue
    languages = list(PDFDocument.objects.values('language').annotate(
        count=Count('language')
    ).order_by('-count')[:10])
    
    # Répartition par thématique
    themes = list(PDFDocument.objects.values('theme').annotate(
        count=Count('theme')
    ).order_by('-count')[:10])
    
    # Évolution temporelle (documents créés par jour)
    from django.db.models import TruncDate
    daily_stats = list(PDFDocument.objects.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')[-30:])  # 30 derniers jours
    
    data = {
        'languages': languages,
        'themes': themes,
        'daily_stats': daily_stats,
        'total_documents': PDFDocument.objects.count(),
        'processed_documents': PDFDocument.objects.filter(is_processed=True).count(),
    }
    
    return JsonResponse(data)

@staff_member_required
def export_pdf_data(request):
    """
    Exporte les données des PDFs au format CSV.
    """
    import csv
    from django.utils import timezone
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="pdf_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Nom du fichier', 'Chemin', 'Langue', 'Thématique', 'Confiance',
        'Taille (MB)', 'Pages', 'Répertoire source', 'Traité', 'Retenu',
        'Date création', 'Date traitement'
    ])
    
    for pdf in PDFDocument.objects.all():
        writer.writerow([
            pdf.filename,
            pdf.file_path,
            pdf.language or 'N/A',
            pdf.theme or 'N/A',
            pdf.confidence,
            pdf.file_size_mb,
            pdf.page_count,
            pdf.source_directory or 'N/A',
            'Oui' if pdf.is_processed else 'Non',
            'Oui' if pdf.is_retained else 'Non',
            pdf.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            pdf.processed_at.strftime('%Y-%m-%d %H:%M:%S') if pdf.processed_at else 'N/A'
        ])
    
    return response

def search_pdf_content(request):
    """
    Recherche dans le contenu des PDFs.
    """
    query = request.GET.get('q', '')
    results = []
    
    if query and len(query) >= 3:
        pdf_docs = PDFDocument.objects.filter(
            content__icontains=query,
            extraction_success=True
        )[:20]
        
        for pdf in pdf_docs:
            # Extraire un contexte autour du terme recherché
            content = pdf.content or ''
            query_lower = query.lower()
            content_lower = content.lower()
            
            index = content_lower.find(query_lower)
            if index != -1:
                start = max(0, index - 100)
                end = min(len(content), index + len(query) + 100)
                context = content[start:end]
                
                results.append({
                    'id': pdf.id,
                    'filename': pdf.filename,
                    'language': pdf.language,
                    'theme': pdf.theme,
                    'context': context,
                    'url': pdf.get_absolute_url()
                })
    
    return JsonResponse({
        'query': query,
        'results': results,
        'count': len(results)
    })