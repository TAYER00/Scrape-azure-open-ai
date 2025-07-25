# 🌐 Gestion Automatique des Sites Web et Relations

Cette solution automatise la gestion des sites web dans la base de données SQLite et établit automatiquement les relations entre les tables `scraper_website` et `scraper_scrapedpdf`.

## 📋 Vue d'ensemble

### Problème Résolu
- **Insertion dynamique** des sites web dans `scraper_website` si non présents
- **Extraction automatique** du nom de domaine à partir des chemins de fichiers
- **Mise à jour automatique** des relations `website_id` dans `scraper_scrapedpdf`
- **Vérification de l'intégrité** des données

### Structure de la Base de Données

```sql
-- Table des sites web
CREATE TABLE scraper_website (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),           -- ex: "agriculture.gov.ma"
    url VARCHAR(200),            -- ex: "https://www.agriculture.gov.ma"
    created_at DATETIME
);

-- Table des PDFs scrapés
CREATE TABLE scraper_scrapedpdf (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500),
    url VARCHAR(200),
    file_path VARCHAR(500),      -- Chemin complet du fichier
    downloaded_at DATETIME,
    website_id INTEGER,          -- Clé étrangère vers scraper_website
    FOREIGN KEY (website_id) REFERENCES scraper_website(id)
);
```

## 🔧 Scripts Disponibles

### 1. `reorganize_database.py` (Script Principal)

**Fonctionnalités:**
- ✅ Création automatique des sites web manquants
- ✅ Ajout des fichiers PDF avec relations correctes
- ✅ Mise à jour des relations existantes
- ✅ Gestion des doublons
- ✅ Logging détaillé

**Utilisation:**
```bash
python reorganize_database.py
```

**Mapping des Sites:**
```python
site_path_map = {
    "agriculture.gov.ma": r"agriculture.gov.ma\\pdf_downloads",
    "bkam.ma": [
        r"bkam.ma\\bkam.ma\\pdf_downloads\\Communiques\\pdf_scraper",
        r"bkam.ma\\bkam.ma\\pdf_downloads\\Discours\\pdf_scraper"
    ],
    "cese.ma": r"cese.ma\\pdf_downloads",
    "finances.gov.ma": r"finances.gov.ma\\pdf_downloads",
    "oecd.org": r"oecd.org\\pdf_downloads"
}
```

### 2. `manage_websites.py` (Gestion Spécialisée)

**Fonctionnalités:**
- 🎯 Focus sur la gestion des sites web et relations
- 🔄 Mise à jour des `website_id` manquants
- 📊 Statistiques détaillées

**Utilisation:**
```bash
python manage_websites.py
```

### 3. `verify_website_relations.py` (Vérification)

**Fonctionnalités:**
- 📊 Statistiques par site web
- 🔍 Détection des PDFs orphelins
- ✅ Vérification de l'intégrité des relations
- 📋 Exemples de données

**Utilisation:**
```bash
python verify_website_relations.py
```

### 4. `demo_website_management.py` (Démonstration)

**Fonctionnalités:**
- 🎓 Exemples d'utilisation
- 🧪 Tests des fonctions d'extraction
- 📝 Requêtes SQL utiles
- 💡 Conseils d'utilisation

**Utilisation:**
```bash
python demo_website_management.py
```

## 🚀 Guide d'Utilisation

### Utilisation Complète (Recommandée)

```bash
# 1. Traitement complet avec gestion automatique
python reorganize_database.py

# 2. Vérification des résultats
python verify_website_relations.py
```

### Utilisation Spécialisée

```bash
# Gestion uniquement des sites et relations
python manage_websites.py

# Démonstration et exemples
python demo_website_management.py
```

## 📊 Exemple de Sortie

### Execution de `reorganize_database.py`:
```
🚀 Démarrage du remplissage de la table scraper_scrapedpdf avec gestion des sites web

=== Étape 1: Création des sites web ===
✅ Site web créé : agriculture.gov.ma
✅ Site web créé : bkam.ma
✅ Site web créé : cese.ma
✅ Site web créé : finances.gov.ma
✅ Site web créé : oecd.org
Sites web créés : 5

=== Étape 2: Ajout des fichiers PDF ===
Sites web disponibles : ['agriculture.gov.ma', 'bkam.ma', 'cese.ma', 'finances.gov.ma', 'oecd.org']
✅ PDF ajouté : document1.pdf (site: agriculture.gov.ma, ID: 1)
✅ PDF ajouté : rapport.pdf (site: bkam.ma, ID: 2)
...

=== Résumé ===
Ajoutés : 351
Ignorés (doublons) : 0

=== Étape 3: Mise à jour des relations existantes ===
Mis à jour : 0
Erreurs : 0

✅ Traitement terminé avec succès
```

### Execution de `verify_website_relations.py`:
```
=== Sites web dans la base ===
ID: 1 | Nom: agriculture.gov.ma | URL: https://www.agriculture.gov.ma
ID: 2 | Nom: bkam.ma | URL: https://www.bkam.ma
...

=== Statistiques des PDFs par site ===
📊 agriculture.gov.ma: 255 PDFs
📊 bkam.ma: 44 PDFs
📊 oecd.org: 23 PDFs
📊 cese.ma: 17 PDFs
📊 finances.gov.ma: 12 PDFs

📈 Total PDFs: 351
⚠️ PDFs sans website_id: 0

=== RÉSUMÉ ===
Sites web configurés: 5
PDFs avec relations: 351
PDFs orphelins: 0
Références invalides: 0
🎉 Toutes les relations sont correctement configurées !
```

## 🔍 Fonctions Clés

### Extraction de Nom de Site

```python
def extract_site_name_from_path(file_path):
    """Extrait le nom du site à partir du chemin du fichier"""
    # Utilise le mapping site_path_map pour identifier le site
    # Fallback sur l'analyse du premier dossier du chemin
    return site_name
```

**Exemples:**
- `agriculture.gov.ma\pdf_downloads\doc.pdf` → `agriculture.gov.ma`
- `bkam.ma\bkam.ma\pdf_downloads\Communiques\pdf_scraper\rapport.pdf` → `bkam.ma`

### Requêtes SQL Utiles

```sql
-- PDFs par site avec comptage
SELECT w.name, COUNT(p.id) as pdf_count
FROM scraper_website w
LEFT JOIN scraper_scrapedpdf p ON w.id = p.website_id
GROUP BY w.id, w.name
ORDER BY pdf_count DESC;

-- PDFs sans relation (orphelins)
SELECT COUNT(*) 
FROM scraper_scrapedpdf 
WHERE website_id IS NULL;

-- Recherche par site et mot-clé
SELECT w.name, p.title
FROM scraper_scrapedpdf p
JOIN scraper_website w ON p.website_id = w.id
WHERE w.name = 'agriculture.gov.ma' 
AND p.title LIKE '%Dahir%';
```

## ⚙️ Configuration

### Ajout d'un Nouveau Site

1. **Modifier le mapping dans `reorganize_database.py`:**
```python
site_path_map = {
    # Sites existants...
    "nouveau-site.gov.ma": r"nouveau-site.gov.ma\\pdf_downloads"
}
```

2. **Ajouter le site dans `ensure_websites_exist()`:**
```python
websites = [
    # Sites existants...
    {"name": "nouveau-site.gov.ma", "url": "https://www.nouveau-site.gov.ma"}
]
```

3. **Exécuter le script:**
```bash
python reorganize_database.py
```

## 🛠️ Maintenance

### Vérifications Régulières

```bash
# Vérification hebdomadaire
python verify_website_relations.py

# Mise à jour après ajout de nouveaux PDFs
python manage_websites.py
```

### Résolution de Problèmes

**PDFs orphelins détectés:**
```bash
# Mise à jour des relations manquantes
python manage_websites.py
```

**Nouveau site non reconnu:**
1. Ajouter le site au mapping `site_path_map`
2. Relancer `reorganize_database.py`

## 📈 Statistiques Typiques

- **Sites web gérés:** 5 (agriculture.gov.ma, bkam.ma, cese.ma, finances.gov.ma, oecd.org)
- **PDFs traités:** 351+
- **Taux de liaison:** 100% (aucun PDF orphelin)
- **Performance:** ~1-2 secondes pour 351 PDFs

## 🔒 Sécurité et Intégrité

- ✅ **Gestion des doublons** automatique
- ✅ **Validation des références** website_id
- ✅ **Transactions atomiques** pour la cohérence
- ✅ **Logging détaillé** pour le debugging
- ✅ **Gestion d'erreurs** robuste

## 🎯 Avantages

1. **Automatisation complète** - Plus besoin de gérer manuellement les sites
2. **Intégrité des données** - Relations toujours cohérentes
3. **Extensibilité** - Facile d'ajouter de nouveaux sites
4. **Monitoring** - Outils de vérification intégrés
5. **Performance** - Traitement rapide même avec de gros volumes

---

**Auteur:** Assistant IA  
**Date:** 2025-07-25  
**Version:** 1.0