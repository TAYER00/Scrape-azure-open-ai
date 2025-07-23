from django.urls import path
from . import views
from . import pdf_views
from . import pdf_analysis_views

app_name = 'scraper'

urlpatterns = [
    path('', views.home, name='home'),
    path('bkam/communiques/', views.bkam_communiques, name='bkam_communiques'),
    path('bkam/discours/', views.bkam_discours, name='bkam_discours'),
    path('agriculture/', views.agriculture_documents, name='agriculture_documents'),
    path('cese/', views.cese_documents, name='cese_documents'),
    path('finances/', views.finances_documents, name='finances_documents'),
    path('oecd/', views.oecd_documents, name='oecd_documents'),
    
    # URLs pour télécharger les fichiers Word
    path('<str:site>/words_downloads/<str:filename>', views.download_word_file, name='download_word_file'),
    
    # URLs pour les PDFs avec configuration media
    path('pdfs/', pdf_views.pdf_list_view, name='pdf_list'),
    path('pdfs/<str:category>/', pdf_views.pdf_list_view, name='pdf_list_category'),
    path('pdf/view/<str:filename>/', pdf_views.pdf_viewer_view, name='pdf_viewer'),
    path('pdf/serve/<str:filename>/', pdf_views.serve_pdf, name='serve_pdf'),
    path('pdf/download/<str:filename>/', pdf_views.pdf_download_view, name='pdf_download'),
    path('pdf/demo/', pdf_views.pdf_demo_view, name='pdf_demo'),
    
    # PDF Analysis URLs
    path('pdf-documents/', pdf_analysis_views.PDFDocumentListView.as_view(), name='pdf_document_list'),
    path('pdf-documents/<int:pk>/', pdf_analysis_views.PDFDocumentDetailView.as_view(), name='pdf_detail'),
    path('pdf-dashboard/', pdf_analysis_views.pdf_dashboard, name='pdf_dashboard'),
    path('pdf-documents/<int:pk>/reprocess/', pdf_analysis_views.reprocess_pdf, name='reprocess_pdf'),
    path('pdf-documents/<int:pk>/toggle-retained/', pdf_analysis_views.toggle_retained, name='toggle_retained'),
    path('api/pdf-stats/', pdf_analysis_views.pdf_stats_api, name='pdf_stats_api'),
    path('export/pdf-data/', pdf_analysis_views.export_pdf_data, name='export_pdf_data'),
    path('search/pdf-content/', pdf_analysis_views.search_pdf_content, name='search_pdf_content'),
]