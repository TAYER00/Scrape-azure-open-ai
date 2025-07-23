#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_scraper.settings')
django.setup()

from scraper.models import PDFDocument

print(f'Nombre de PDFs dans la base: {PDFDocument.objects.count()}')
print('\nPremiers PDFs:')
for pdf in PDFDocument.objects.all()[:5]:
    print(f'- {pdf.filename}')
    print(f'  Langue: {pdf.language or "Non analysé"}')
    print(f'  Thème: {pdf.theme or "Non analysé"}')
    print(f'  Traité: {pdf.is_processed}')
    print()

if PDFDocument.objects.count() == 0:
    print('Aucun PDF trouvé. Vous pouvez utiliser la commande:')
    print('python manage.py process_pdfs --scan-only')
    print('pour scanner les répertoires et trouver des PDFs à analyser.')