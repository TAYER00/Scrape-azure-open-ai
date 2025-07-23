# Système d'Analyse PDF avec Azure OpenAI

Ce système permet de lire, extraire et analyser automatiquement le contenu de fichiers PDF en utilisant Azure OpenAI pour détecter la langue et la thématique des documents.

## 🚀 Fonctionnalités

- **Extraction de texte** : Lecture automatique du contenu des fichiers PDF
- **Analyse IA** : Détection de la langue et de la thématique via Azure OpenAI
- **Interface web** : Dashboard et interface de gestion des documents
- **Traitement en lot** : Commande Django pour traiter plusieurs PDFs
- **Filtrage et recherche** : Interface avancée pour explorer les documents
- **Export de données** : Export CSV des résultats d'analyse

## 📁 Structure du Projet

```
├── .env                           # Configuration Azure OpenAI
├── requirements.txt               # Dépendances Python
├── scraper/
│   ├── models.py                 # Modèle PDFDocument
│   ├── pdf_analysis_views.py     # Vues pour l'analyse PDF
│   ├── management/commands/
│   │   └── process_pdfs.py       # Commande de traitement
│   └── templates/scraper/
│       ├── pdf_dashboard.html    # Tableau de bord
│       ├── pdf_documents_list.html # Liste des documents
│       └── pdf_document_detail.html # Détails d'un document
└── utils/
    ├── pdf_tools.py              # Outils d'extraction PDF
    └── openai_client.py          # Client Azure OpenAI
```

## ⚙️ Configuration

### 1. Variables d'environnement (.env)

```env
AZURE_OPENAI_ENDPOINT=https://cog-7hu3jtoolb2i6.openai.azure.com/
AZURE_OPENAI_API_KEY=3ab2614ffb144a67b397c431ca35af44
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo

DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Migrations de base de données

```bash
python manage.py makemigrations
python manage.py migrate
```

## 🔧 Utilisation

### Commande de traitement des PDFs

```bash
# Traiter tous les PDFs des répertoires par défaut
python manage.py process_pdfs

# Traiter un répertoire spécifique
python manage.py process_pdfs --directory "path/to/pdf/folder"

# Traiter un fichier spécifique
python manage.py process_pdfs --file "path/to/file.pdf"

# Simulation sans traitement réel
python manage.py process_pdfs --dry-run

# Retraiter les PDFs déjà traités
python manage.py process_pdfs --force

# Extraire seulement le texte (sans analyse OpenAI)
python manage.py process_pdfs --skip-analysis

# Limiter le nombre de fichiers traités
python manage.py process_pdfs --max-files 10
```

### Répertoires par défaut

Le système scanne automatiquement ces répertoires :
- `bkam.ma/bkam.ma/pdf_downloads/Communiques/pdf_scraper`
- `bkam.ma/bkam.ma/pdf_downloads/Discours/pdf_scraper`
- `cese.ma/pdf_downloads`
- `finances.gov.ma/pdf_downloads`
- `oecd.org/pdf_downloads`

## 🌐 Interface Web

### URLs disponibles

- `/pdf-dashboard/` : Tableau de bord avec statistiques
- `/pdf-documents/` : Liste des documents avec filtres
- `/pdf-documents/<id>/` : Détails d'un document
- `/api/pdf-stats/` : API des statistiques (JSON)
- `/export/pdf-data/` : Export CSV des données
- `/search/pdf-content/` : Recherche dans le contenu

### Fonctionnalités de l'interface

1. **Tableau de bord** :
   - Statistiques générales
   - Graphiques de répartition par langue et thématique
   - Documents récents
   - Actions rapides

2. **Liste des documents** :
   - Filtrage par langue, thématique, statut
   - Recherche textuelle
   - Tri par différents critères
   - Actions en lot

3. **Détails d'un document** :
   - Métadonnées complètes
   - Contenu extrait
   - Résultats d'analyse OpenAI
   - Actions (retraitement, favoris)

## 🤖 Analyse OpenAI

### Informations extraites

- **Langue** : Langue principale du document
- **Thématique** : Sujet principal du document
- **Confiance** : Score de confiance de l'analyse (0-100%)
- **Résumé** : Résumé automatique du contenu

### Configuration de l'analyse

```python
# Dans settings.py
PDF_PROCESSING = {
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB
    'MAX_CONTENT_LENGTH': 100000,       # 100k caractères
    'SUPPORTED_LANGUAGES': ['fr', 'en', 'ar'],
    'BATCH_SIZE': 10,
}
```

## 📊 Modèle de données

### PDFDocument

```python
class PDFDocument(models.Model):
    # Informations de base
    filename = models.CharField(max_length=255)
    file_path = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    
    # Contenu extrait
    content = models.TextField(blank=True, null=True)
    content_length = models.IntegerField(default=0)
    
    # Analyse OpenAI
    language = models.CharField(max_length=50, blank=True, null=True)
    theme = models.CharField(max_length=200, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    
    # Métadonnées
    file_size = models.BigIntegerField(blank=True, null=True)
    page_count = models.IntegerField(blank=True, null=True)
    source_directory = models.TextField(blank=True, null=True)
    
    # Statuts de traitement
    is_processed = models.BooleanField(default=False)
    extraction_success = models.BooleanField(default=False)
    openai_analysis_success = models.BooleanField(default=False)
    is_retained = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
```

## 🔍 Dépannage

### Erreurs courantes

1. **Module 'fitz' not found** :
   ```bash
   pip install PyMuPDF
   ```

2. **Erreur Azure OpenAI** :
   - Vérifiez les variables d'environnement
   - Vérifiez la validité de la clé API
   - Vérifiez le nom du déploiement

3. **Fichier PDF non lisible** :
   - Vérifiez que le fichier n'est pas corrompu
   - Vérifiez les permissions de lecture
   - Vérifiez la taille du fichier (limite : 50MB)

### Logs

Les logs sont configurés dans `settings.py` et sauvegardés dans le dossier `logs/` :
- `logs/pdf_tools.log` : Extraction de texte
- `logs/openai_client.log` : Analyse OpenAI
- `logs/process_pdfs.log` : Commande de traitement

## 📈 Performance

### Optimisations

- Traitement par lots configurable
- Cache des résultats d'analyse
- Pagination des listes
- Indexation de la base de données

### Limites

- Taille maximale par fichier : 50MB
- Longueur maximale du contenu : 100k caractères
- Taille de lot par défaut : 10 fichiers

## 🚀 Démarrage rapide

1. **Configuration** :
   ```bash
   cp .env.example .env
   # Éditer .env avec vos clés Azure
   ```

2. **Installation** :
   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   ```

3. **Traitement des PDFs** :
   ```bash
   python manage.py process_pdfs --max-files 5
   ```

4. **Lancement du serveur** :
   ```bash
   python manage.py runserver
   ```

5. **Accès à l'interface** :
   - Tableau de bord : http://127.0.0.1:8000/pdf-dashboard/
   - Liste des documents : http://127.0.0.1:8000/pdf-documents/

## 📝 Notes importantes

- Assurez-vous que les répertoires PDF existent avant le traitement
- Les clés Azure OpenAI doivent être valides et actives
- Le traitement peut prendre du temps selon le nombre et la taille des fichiers
- Utilisez `--dry-run` pour tester avant le traitement réel
- Les documents déjà traités sont ignorés (utilisez `--force` pour retraiter)

## 🔗 Liens utiles

- [Documentation Django](https://docs.djangoproject.com/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)