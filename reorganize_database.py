#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour réorganiser la base de données SQLite :
1. Renommer la table scraper_pdfdocument en scraper_wordsdocument
2. Supprimer tous les enregistrements liés aux fichiers .pdf
3. Ajouter les fichiers .docx des répertoires spécifiés
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Obtenir une connexion à la base de données SQLite"""
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        logger.error(f"Base de données non trouvée : {db_path}")
        return None
    return sqlite3.connect(db_path)

def rename_table(conn):
    """Étape 1 : Renommer la table scraper_pdfdocument en scraper_wordsdocument"""
    try:
        cursor = conn.cursor()
        
        # Vérifier si la table scraper_pdfdocument existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scraper_pdfdocument'
        """)
        
        if cursor.fetchone():
            # Vérifier si scraper_wordsdocument existe déjà
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='scraper_wordsdocument'
            """)
            
            if cursor.fetchone():
                logger.info("La table scraper_wordsdocument existe déjà, suppression...")
                cursor.execute("DROP TABLE scraper_wordsdocument")
            
            # Renommer la table
            cursor.execute("ALTER TABLE scraper_pdfdocument RENAME TO scraper_wordsdocument")
            logger.info("✅ Table renommée : scraper_pdfdocument → scraper_wordsdocument")
        else:
            logger.warning("Table scraper_pdfdocument non trouvée")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du renommage de la table : {e}")
        return False

def clean_pdf_records(conn):
    """Étape 2 : Supprimer tous les enregistrements liés aux fichiers .pdf"""
    try:
        cursor = conn.cursor()
        
        # Compter les enregistrements PDF avant suppression
        cursor.execute("""
            SELECT COUNT(*) FROM scraper_wordsdocument 
            WHERE filename LIKE '%.pdf' OR filename LIKE '%.pdf.%'
        """)
        pdf_count = cursor.fetchone()[0]
        
        if pdf_count > 0:
            # Supprimer les enregistrements PDF
            cursor.execute("""
                DELETE FROM scraper_wordsdocument 
                WHERE filename LIKE '%.pdf' OR filename LIKE '%.pdf.%'
            """)
            logger.info(f"✅ {pdf_count} enregistrements PDF supprimés")
        else:
            logger.info("Aucun enregistrement PDF trouvé")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des enregistrements PDF : {e}")
        return False

def get_file_size(file_path):
    """Obtenir la taille d'un fichier"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def add_docx_files(conn):
    """Étape 3 : Ajouter les fichiers .docx des répertoires spécifiés"""
    directories = [
        r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\finances.gov.ma\words_downloads',
        r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\cese.ma\pdf_downloads',
        r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\agriculture.gov.ma\words_downloads',
        r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\oecd.org\words_downloads',
        r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\bkam.ma\bkam.ma\pdf_downloads\Communiques\words_downloads',
        r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\bkam.ma\bkam.ma\pdf_downloads\Discours\words_downloads'
    ]
    
    try:
        cursor = conn.cursor()
        
        # Obtenir la liste des fichiers déjà présents
        cursor.execute("SELECT filename FROM scraper_wordsdocument")
        existing_files = {row[0] for row in cursor.fetchall()}
        
        added_count = 0
        skipped_count = 0
        
        for directory in directories:
            if not os.path.exists(directory):
                logger.warning(f"Répertoire non trouvé : {directory}")
                continue
            
            logger.info(f"Scan du répertoire : {directory}")
            
            # Chercher tous les fichiers .docx
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.docx'):
                        full_path = os.path.join(root, file)
                        
                        # Vérifier si le fichier existe déjà
                        if file in existing_files:
                            logger.debug(f"Fichier déjà présent : {file}")
                            skipped_count += 1
                            continue
                        
                        # Obtenir les métadonnées du fichier
                        file_size = get_file_size(full_path)
                        source_dir = os.path.basename(os.path.dirname(directory))
                        
                        # Insérer le nouveau fichier
                        cursor.execute("""
                            INSERT INTO scraper_wordsdocument (
                                filename, file_path, file_size, source_directory,
                                is_processed, extraction_success, analysis_success,
                                content, content_length, language, theme, confidence,
                                summary, error_message, is_retained, page_count,
                                created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            file,
                            full_path,
                            file_size,
                            source_dir,
                            False,  # is_processed
                            False,  # extraction_success
                            False,  # analysis_success
                            "",     # content
                            0,      # content_length
                            None,   # language
                            None,   # theme
                            "Moyen", # confidence
                            "",     # summary
                            None,   # error_message
                            True,   # is_retained
                            0,      # page_count
                            datetime.now().isoformat(),  # created_at
                            datetime.now().isoformat()   # updated_at
                        ))
                        
                        added_count += 1
                        existing_files.add(file)  # Ajouter à la liste pour éviter les doublons
                        logger.info(f"✅ Ajouté : {file}")
        
        conn.commit()
        logger.info(f"\n=== RÉSUMÉ AJOUT FICHIERS ===")
        logger.info(f"Fichiers ajoutés : {added_count}")
        logger.info(f"Fichiers ignorés (doublons) : {skipped_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des fichiers .docx : {e}")
        return False

def get_table_stats(conn):
    """Obtenir les statistiques de la table"""
    try:
        cursor = conn.cursor()
        
        # Compter le total
        cursor.execute("SELECT COUNT(*) FROM scraper_wordsdocument")
        total = cursor.fetchone()[0]
        
        # Compter par extension
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN filename LIKE '%.docx' THEN 'DOCX'
                    WHEN filename LIKE '%.pdf' THEN 'PDF'
                    ELSE 'AUTRE'
                END as type,
                COUNT(*) as count
            FROM scraper_wordsdocument 
            GROUP BY type
        """)
        
        stats = cursor.fetchall()
        
        logger.info(f"\n=== STATISTIQUES FINALES ===")
        logger.info(f"Total d'enregistrements : {total}")
        for stat_type, count in stats:
            logger.info(f"{stat_type} : {count}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention des statistiques : {e}")

def main():
    """Fonction principale"""
    logger.info("🚀 Début de la réorganisation de la base de données")
    
    # Connexion à la base de données
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        # Étape 1 : Renommer la table
        logger.info("\n🧩 ÉTAPE 1 : Renommage de la table")
        if not rename_table(conn):
            logger.error("Échec du renommage de la table")
            return
        
        # Étape 2 : Nettoyer les données PDF
        logger.info("\n🧹 ÉTAPE 2 : Nettoyage des données PDF")
        if not clean_pdf_records(conn):
            logger.error("Échec du nettoyage des données PDF")
            return
        
        # Étape 3 : Ajouter les fichiers .docx
        logger.info("\n📥 ÉTAPE 3 : Ajout des fichiers .docx")
        if not add_docx_files(conn):
            logger.error("Échec de l'ajout des fichiers .docx")
            return
        
        # Statistiques finales
        get_table_stats(conn)
        
        logger.info("\n✅ Réorganisation terminée avec succès !")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()