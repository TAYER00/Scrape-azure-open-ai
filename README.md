# 🌐 Plateforme de Scraping et d'Analyse de Documents Gouvernementaux Marocains

Ce projet est une plateforme complète de scraping, conversion et analyse intelligente de documents PDF/Word provenant de sites gouvernementaux marocains. Il combine web scraping, traitement de documents, analyse par IA (Azure OpenAI) et interface web Django.

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du Projet](#architecture-du-projet)
3. [Pipeline de Traitement](#pipeline-de-traitement)
4. [Installation et Configuration](#installation-et-configuration)
5. [Guide d'Utilisation](#guide-dutilisation)
6. [Structure des Données](#structure-des-données)
7. [Interface Web](#interface-web)
8. [Extensions Possibles](#extensions-possibles)

## 🎯 Vue d'ensemble

La plateforme traite automatiquement les documents de 5 sites gouvernementaux :
- **Bank Al-Maghrib** (bkam.ma) - Banque centrale
- **CESE** (cese.ma) - Conseil Économique, Social et Environnemental
- **Ministère des Finances** (finances.gov.ma)
- **Ministère de l'Agriculture** (agriculture.gov.ma)
- **OCDE** (oecd.org) - Organisation de Coopération et de Développement Économiques

### Fonctionnalités Principales
- ✅ Scraping automatisé de documents PDF
- ✅ Conversion PDF → Word (.docx)
- ✅ Analyse intelligente par Azure OpenAI (langue, thème, résumé)
- ✅ Interface web Django avec dashboard
- ✅ Base de données SQLite pour la gestion des métadonnées
- ✅ Export des résultats en JSON

## 🏗️ Architecture du Projet

```
📁 Scraping-web-sites-auto-naviguation-master/
├── 🌐 Sites de scraping/
│   ├── agriculture.gov.ma/
│   │   ├── scraper.py
│   │   ├── pdf_downloads/          # PDFs téléchargés
│   │   └── words_downloads/        # Fichiers .docx convertis
│   ├── bkam.ma/
│   ├── cese.ma/
│   ├── finances.gov.ma/
│   └── oecd.org/
├── 🔧 Scripts de traitement/
│   ├── run_all_scrapers.py         # Gestionnaire de scrapers
│   ├── convert_pdfs_to_word.py     # Conversion PDF → Word
│   ├── add_word_documents.py       # Ajout documents en DB
│   ├── reorganize_database.py      # Réorganisation DB
│   ├── analyze_word_documents.py   # Analyse IA
│   └── check_pdfs.py              # Vérification DB
├── 🌐 Interface Django/
│   ├── web_scraper/               # Configuration Django
│   ├── scraper/                   # App principale
│   │   ├── models.py             # Modèles de données
│   │   ├── views.py              # Vues web
│   │   └── management/commands/   # Commandes Django
│   └── utils/                     # Utilitaires (PDF, OpenAI)
├── 📊 Données/
│   ├── db.sqlite3                # Base de données
│   └── result.json               # Résultats d'analyse
└── 📋 Configuration/
    ├── requirements.txt
    ├── .env                      # Variables d'environnement
    └── manage.py
```

## 🔄 Pipeline de Traitement

### Étape 1 : Scraping des Documents
**Script :** `run_all_scrapers.py`

Lance tous les scrapers en parallèle dans des terminaux séparés.

```bash
python run_all_scrapers.py
```

**Fonctionnalités :**
- Interface interactive pour gérer les scrapers
- Lancement en parallèle de 5 scrapers
- Gestion des processus PowerShell
- Téléchargement automatique des PDFs

### Étape 2 : Conversion PDF → Word
**Script :** `convert_pdfs_to_word.py`

Convertit tous les PDFs téléchargés en fichiers Word (.docx) pour faciliter l'extraction de texte.

```bash
python convert_pdfs_to_word.py
```

**Résultat :** Fichiers .docx dans les dossiers `words_downloads/` de chaque site.

### Étape 3 : Ajout en Base de Données
**Script :** `add_word_documents.py`

Scanne les répertoires et ajoute les documents Word à la base de données.

```bash
python add_word_documents.py
```

**Fonctionnalités :**
- Évite les doublons
- Calcule les métadonnées (taille, nombre de pages)
- Organise par répertoire source

### Étape 4 : Réorganisation de la Base
**Script :** `reorganize_database.py`

Nettoie et restructure la base de données.

```bash
python reorganize_database.py
```

**Actions :**
1. Renomme `scraper_pdfdocument` → `scraper_wordsdocument`
2. Supprime les enregistrements PDF
3. Ajoute les nouveaux documents Word
4. Évite les doublons

### Étape 5 : Analyse Intelligente
**Script :** `analyze_word_documents.py`

Analyse chaque document avec Azure OpenAI pour déterminer la langue, le thème et générer un résumé.

```bash
python analyze_word_documents.py
```

**Résultat :** Fichier `result.json` avec l'analyse complète.

### Étape 6 : Vérification
**Script :** `check_pdfs.py`

Vérifie l'état de la base de données et affiche les statistiques.

```bash
python check_pdfs.py
```

## ⚙️ Installation et Configuration

### Prérequis
- Python 3.8+
- Compte Azure OpenAI
- Git

### Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd Scraping-web-sites-auto-naviguation-master
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Installer Playwright**
```bash
playwright install
```

4. **Configuration des variables d'environnement**

Créer/modifier le fichier `.env` :
```env
# Configuration Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://votre-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=votre-clé-api
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo

# Configuration Django
DEBUG=True
SECRET_KEY=votre-clé-secrète
DATABASE_URL=sqlite:///db.sqlite3
```

5. **Initialiser Django**
```bash
python manage.py migrate
python manage.py collectstatic
```

### Dépendances Principales
- **Django 5.2.4** - Framework web
- **BeautifulSoup4** - Parsing HTML
- **Playwright** - Automation navigateur
- **PyMuPDF** - Traitement PDF
- **OpenAI** - Client Azure OpenAI
- **pdf2docx** - Conversion PDF → Word
- **python-docx** - Lecture fichiers Word
- **langdetect** - Détection de langue
- **transformers** - Modèles de résumé

## 📖 Guide d'Utilisation

### Utilisation Complète (Pipeline Complet)

```bash
# 1. Scraping des documents
python run_all_scrapers.py

# 2. Conversion PDF → Word
python convert_pdfs_to_word.py

# 3. Ajout en base de données
python add_word_documents.py

# 4. Réorganisation de la base
python reorganize_database.py

# 5. Analyse intelligente
python analyze_word_documents.py

# 6. Vérification des résultats
python check_pdfs.py
```

### Interface Web Django

```bash
# Lancer le serveur de développement
python manage.py runserver

# Accéder à l'interface
# http://127.0.0.1:8000/
```

### Commandes Django Avancées

```bash
# Traitement des PDFs avec Django
python manage.py process_pdfs --directory path/to/pdfs
python manage.py process_pdfs --file specific_file.pdf
python manage.py process_pdfs --max-files 10 --dry-run

# Gestion de la base de données
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
```

## 📊 Structure des Données

### Modèle PDFDocument

La base de données utilise le modèle `PDFDocument` pour stocker les métadonnées :

```python
class PDFDocument(models.Model):
    # Informations de base
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    url = models.URLField(blank=True, null=True)
    
    # Contenu extrait
    content = models.TextField(blank=True, null=True)
    content_length = models.IntegerField(default=0)
    
    # Analyse OpenAI
    language = models.CharField(max_length=50, blank=True, null=True)
    theme = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.CharField(max_length=20, default='Moyen')
    summary = models.TextField(blank=True, null=True)
    
    # Métadonnées
    file_size = models.BigIntegerField(default=0)
    page_count = models.IntegerField(default=0)
    source_directory = models.CharField(max_length=200, blank=True, null=True)
    
    # Statuts de traitement
    is_processed = models.BooleanField(default=False)
    extraction_success = models.BooleanField(default=False)
    analysis_success = models.BooleanField(default=False)
```

### Format du Fichier result.json

```json
[
    {
        "filename": "document.docx",
        "file_path": "/path/to/document.docx",
        "summary": "Résumé généré par IA...",
        "language": "fr",
        "theme": "Économie",
        "extraction_success": true
    }
]
```

## 🌐 Interface Web

### Pages Disponibles

- **Dashboard Principal** (`/`) - Vue d'ensemble des documents
- **Liste des Documents** (`/pdfs/`) - Liste paginée avec filtres
- **Détails Document** (`/pdfs/<id>/`) - Métadonnées complètes
- **Recherche** (`/search/`) - Recherche dans le contenu
- **Administration** (`/admin/`) - Interface d'administration Django

### Fonctionnalités Web

- 📊 **Dashboard** avec statistiques
- 🔍 **Recherche** dans le contenu des documents
- 🏷️ **Filtrage** par langue, thème, source
- 📄 **Pagination** des résultats
- 📱 **Interface responsive** (Bootstrap 5)
- 🔐 **Administration** Django intégrée

## 🔧 Fichiers Clés et Leur Rôle

| Fichier | Rôle | Résultat |
|---------|------|----------|
| `run_all_scrapers.py` | Gestionnaire de scrapers | PDFs téléchargés |
| `convert_pdfs_to_word.py` | Conversion PDF → Word | Fichiers .docx |
| `add_word_documents.py` | Ajout en DB | Enregistrements DB |
| `reorganize_database.py` | Nettoyage DB | DB restructurée |
| `analyze_word_documents.py` | Analyse IA | `result.json` |
| `check_pdfs.py` | Vérification | Statistiques |
| `manage.py` | Interface Django | Serveur web |
| `scraper/models.py` | Modèles de données | Structure DB |
| `utils/pdf_tools.py` | Traitement PDF | Extraction texte |
| `utils/openai_client.py` | Client Azure OpenAI | Analyse IA |

## 🚀 Extensions Possibles

### Améliorations Techniques
- 🔄 **Scraping incrémental** avec détection de nouveaux documents
- 📊 **Analyse de sentiment** avec Azure Cognitive Services
- 🌍 **Support multilingue** étendu (anglais, espagnol)
- 🔍 **Recherche sémantique** avec embeddings
- 📈 **Visualisations** avancées avec Chart.js/D3.js
- 🔔 **Notifications** par email/Slack
- 🐳 **Containerisation** Docker
- ☁️ **Déploiement cloud** (Azure, AWS)

### Nouvelles Fonctionnalités
- 📝 **Classification automatique** par catégories métier
- 🔗 **Détection d'entités** (personnes, organisations, lieux)
- 📊 **Tableaux de bord** personnalisables
- 🔄 **API REST** pour intégration externe
- 📱 **Application mobile** React Native
- 🤖 **Chatbot** pour interroger les documents
- 📧 **Alertes automatiques** sur nouveaux documents

### Optimisations
- ⚡ **Cache Redis** pour les requêtes fréquentes
- 🗄️ **Base de données PostgreSQL** pour la production
- 🔍 **Elasticsearch** pour la recherche full-text
- 📊 **Monitoring** avec Prometheus/Grafana
- 🔐 **Authentification** OAuth2/SAML
- 📈 **Analytics** avec Google Analytics

## 📝 Notes Importantes

- ⚠️ **Clés API** : Configurez vos clés Azure OpenAI dans `.env`
- 🔒 **Sécurité** : Ne commitez jamais le fichier `.env`
- 📊 **Performance** : Le traitement peut être long pour de gros volumes
- 🌐 **Réseau** : Respecte les limites de taux des sites web
- 💾 **Stockage** : Les fichiers Word peuvent être volumineux
- 🔄 **Mise à jour** : Vérifiez régulièrement les dépendances

## 📞 Support

Pour toute question ou problème :
1. Vérifiez les logs dans `logs/pdf_processing.log`
2. Consultez la documentation Django
3. Vérifiez la configuration Azure OpenAI
4. Testez les connexions réseau

---

**Développé avec ❤️ pour l'analyse de documents gouvernementaux marocains**