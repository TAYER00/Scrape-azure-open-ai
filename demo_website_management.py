#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démonstration de la gestion automatique des sites web et relations

Ce script montre comment utiliser les fonctionnalités de gestion des sites web
et des relations website_id dans la base de données SQLite.

Auteur: Assistant IA
Date: 2025-07-25
"""

import sqlite3
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_website_extraction():
    """Démontre l'extraction de noms de sites à partir de chemins de fichiers"""
    logger.info("=== DÉMONSTRATION: Extraction de noms de sites ===")
    
    # Import de la fonction depuis reorganize_database
    from reorganize_database import extract_site_name_from_path
    
    # Exemples de chemins de fichiers
    test_paths = [
        r"agriculture.gov.ma\pdf_downloads\document1.pdf",
        r"bkam.ma\bkam.ma\pdf_downloads\Communiques\pdf_scraper\rapport.pdf",
        r"cese.ma\pdf_downloads\avis.pdf",
        r"finances.gov.ma\pdf_downloads\budget.pdf",
        r"oecd.org\pdf_downloads\study.pdf",
        r"unknown_site\documents\file.pdf"  # Cas d'erreur
    ]
    
    for path in test_paths:
        site_name = extract_site_name_from_path(path)
        status = "✅" if site_name else "❌"
        logger.info(f"{status} {path[:50]}... → {site_name or 'Non détecté'}")

def demo_database_queries():
    """Démontre des requêtes utiles sur la base de données"""
    logger.info("\n=== DÉMONSTRATION: Requêtes de base de données ===")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # 1. Requête: PDFs par site avec comptage
        logger.info("\n📊 Requête 1: Nombre de PDFs par site")
        cursor.execute("""
            SELECT w.name, COUNT(p.id) as count, w.url
            FROM scraper_website w
            LEFT JOIN scraper_scrapedpdf p ON w.id = p.website_id
            GROUP BY w.id, w.name, w.url
            ORDER BY count DESC
        """)
        
        for site_name, count, url in cursor.fetchall():
            logger.info(f"  {site_name}: {count} PDFs ({url})")
        
        # 2. Requête: PDFs récents par site
        logger.info("\n📅 Requête 2: PDFs les plus récents par site")
        cursor.execute("""
            SELECT w.name, p.title, p.downloaded_at
            FROM scraper_scrapedpdf p
            JOIN scraper_website w ON p.website_id = w.id
            ORDER BY p.downloaded_at DESC
            LIMIT 10
        """)
        
        for site_name, title, downloaded_at in cursor.fetchall():
            logger.info(f"  {site_name}: {title[:40]}... ({downloaded_at[:19]})")
        
        # 3. Requête: Recherche de PDFs par mot-clé
        logger.info("\n🔍 Requête 3: Recherche par mot-clé 'Dahir'")
        cursor.execute("""
            SELECT w.name, p.title
            FROM scraper_scrapedpdf p
            JOIN scraper_website w ON p.website_id = w.id
            WHERE p.title LIKE '%Dahir%'
            LIMIT 5
        """)
        
        for site_name, title in cursor.fetchall():
            logger.info(f"  {site_name}: {title}")
        
        # 4. Requête: Statistiques globales
        logger.info("\n📈 Requête 4: Statistiques globales")
        cursor.execute("SELECT COUNT(*) FROM scraper_website")
        website_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scraper_scrapedpdf")
        pdf_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM scraper_scrapedpdf 
            WHERE website_id IS NOT NULL
        """)
        linked_count = cursor.fetchone()[0]
        
        logger.info(f"  Sites web: {website_count}")
        logger.info(f"  PDFs total: {pdf_count}")
        logger.info(f"  PDFs liés: {linked_count}")
        logger.info(f"  Taux de liaison: {(linked_count/pdf_count*100):.1f}%")
        
    except Exception as e:
        logger.error(f"Erreur lors des requêtes: {e}")
    finally:
        conn.close()

def demo_manual_site_creation():
    """Démontre la création manuelle d'un nouveau site web"""
    logger.info("\n=== DÉMONSTRATION: Création manuelle d'un site ===")
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Vérifier si le site existe déjà
        test_site = "example.gov.ma"
        cursor.execute("SELECT id FROM scraper_website WHERE name = ?", (test_site,))
        
        if cursor.fetchone():
            logger.info(f"ℹ️ Le site {test_site} existe déjà")
        else:
            # Créer le nouveau site
            cursor.execute("""
                INSERT INTO scraper_website (name, url, created_at)
                VALUES (?, ?, ?)
            """, (
                test_site,
                f"https://www.{test_site}",
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"✅ Site {test_site} créé avec succès")
            
            # Récupérer l'ID du nouveau site
            cursor.execute("SELECT id FROM scraper_website WHERE name = ?", (test_site,))
            new_id = cursor.fetchone()[0]
            logger.info(f"   ID assigné: {new_id}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la création: {e}")
    finally:
        conn.close()

def demo_usage_examples():
    """Affiche des exemples d'utilisation des scripts"""
    logger.info("\n=== EXEMPLES D'UTILISATION ===")
    
    examples = [
        {
            "title": "1. Remplir la base avec gestion automatique des sites",
            "command": "python reorganize_database.py",
            "description": "Crée automatiquement les sites web et ajoute les PDFs avec relations"
        },
        {
            "title": "2. Gérer uniquement les sites web et relations",
            "command": "python manage_websites.py",
            "description": "Crée les sites web et met à jour les relations existantes"
        },
        {
            "title": "3. Vérifier l'état des relations",
            "command": "python verify_website_relations.py",
            "description": "Affiche des statistiques et vérifie l'intégrité des données"
        },
        {
            "title": "4. Démonstration complète",
            "command": "python demo_website_management.py",
            "description": "Exécute cette démonstration avec exemples et tests"
        }
    ]
    
    for example in examples:
        logger.info(f"\n{example['title']}:")
        logger.info(f"  Commande: {example['command']}")
        logger.info(f"  Description: {example['description']}")

def main():
    """Fonction principale de démonstration"""
    logger.info("🚀 DÉMONSTRATION: Gestion automatique des sites web")
    logger.info("=" * 60)
    
    try:
        # 1. Démonstration de l'extraction de noms de sites
        demo_website_extraction()
        
        # 2. Démonstration des requêtes de base de données
        demo_database_queries()
        
        # 3. Démonstration de création manuelle
        demo_manual_site_creation()
        
        # 4. Exemples d'utilisation
        demo_usage_examples()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Démonstration terminée avec succès")
        logger.info("\n💡 Conseils:")
        logger.info("   - Utilisez reorganize_database.py pour un traitement complet")
        logger.info("   - Utilisez verify_website_relations.py pour vérifier l'état")
        logger.info("   - Les relations sont automatiquement gérées selon les chemins")
        
    except Exception as e:
        logger.error(f"Erreur durant la démonstration: {e}")

if __name__ == '__main__':
    main()