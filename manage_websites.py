import os
import sqlite3
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Connexion à la base de données SQLite"""
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        logger.error(f"Base de données non trouvée : {db_path}")
        return None
    return sqlite3.connect(db_path)

def extract_site_name_from_path(file_path):
    """Extrait le nom du site à partir du chemin du fichier"""
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
    
    # Normaliser le chemin (remplacer les / par \\)
    normalized_path = file_path.replace('/', '\\\\')
    
    for site_name, patterns in site_path_map.items():
        if isinstance(patterns, str):
            patterns = [patterns]
        
        for pattern in patterns:
            if pattern in normalized_path:
                return site_name
    
    # Fallback: extraire le premier dossier du chemin
    parts = file_path.replace('\\', '/').split('/')
    if len(parts) > 0:
        first_part = parts[0]
        # Vérifier si c'est un nom de domaine valide
        if '.' in first_part and any(first_part.endswith(ext) for ext in ['.ma', '.org', '.com', '.gov']):
            return first_part
    
    return None

def ensure_websites_exist(conn):
    """S'assure que tous les sites web nécessaires existent dans la table scraper_website"""
    cursor = conn.cursor()
    
    # Sites web à créer
    websites = [
        {"name": "agriculture.gov.ma", "url": "https://www.agriculture.gov.ma"},
        {"name": "bkam.ma", "url": "https://www.bkam.ma"},
        {"name": "cese.ma", "url": "https://www.cese.ma"},
        {"name": "finances.gov.ma", "url": "https://www.finances.gov.ma"},
        {"name": "oecd.org", "url": "https://www.oecd.org"}
    ]
    
    # Vérifier les sites existants
    cursor.execute("SELECT name FROM scraper_website")
    existing_sites = {row[0] for row in cursor.fetchall()}
    
    created_count = 0
    for website in websites:
        if website["name"] not in existing_sites:
            try:
                cursor.execute("""
                    INSERT INTO scraper_website (name, url, created_at)
                    VALUES (?, ?, ?)
                """, (
                    website["name"],
                    website["url"],
                    datetime.now().isoformat()
                ))
                created_count += 1
                logger.info(f"✅ Site web créé : {website['name']}")
            except Exception as e:
                logger.error(f"Erreur lors de la création du site {website['name']} : {e}")
    
    conn.commit()
    logger.info(f"Sites web créés : {created_count}")
    return created_count

def get_website_id_map(conn):
    """Récupère le mapping nom_site -> id de la table scraper_website"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM scraper_website")
    return {name: id for id, name in cursor.fetchall()}

def update_website_ids(conn):
    """Met à jour les website_id dans scraper_scrapedpdf en fonction des file_path"""
    cursor = conn.cursor()
    
    # Récupérer le mapping des sites
    website_map = get_website_id_map(conn)
    logger.info(f"Sites web disponibles : {list(website_map.keys())}")
    
    # Récupérer tous les enregistrements sans website_id
    cursor.execute("""
        SELECT id, file_path, site_web 
        FROM scraper_scrapedpdf 
        WHERE website_id IS NULL
    """)
    
    records = cursor.fetchall()
    updated_count = 0
    error_count = 0
    
    for record_id, file_path, site_web in records:
        # Essayer d'abord avec le champ site_web s'il existe
        site_name = site_web if site_web else extract_site_name_from_path(file_path)
        
        if site_name and site_name in website_map:
            website_id = website_map[site_name]
            try:
                cursor.execute("""
                    UPDATE scraper_scrapedpdf 
                    SET website_id = ? 
                    WHERE id = ?
                """, (website_id, record_id))
                updated_count += 1
                logger.debug(f"✅ Mis à jour record {record_id} -> site {site_name} (ID: {website_id})")
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du record {record_id} : {e}")
                error_count += 1
        else:
            logger.warning(f"⚠️ Site non trouvé pour le fichier : {file_path} (site détecté: {site_name})")
            error_count += 1
    
    conn.commit()
    logger.info(f"\n=== Résumé des mises à jour ===\nMis à jour : {updated_count}\nErreurs : {error_count}")
    return updated_count, error_count

def main():
    logger.info("🚀 Démarrage de la gestion des sites web et relations")
    conn = get_db_connection()
    if not conn:
        return

    try:
        # 1. S'assurer que tous les sites web existent
        logger.info("\n=== Étape 1: Création des sites web ===")
        ensure_websites_exist(conn)
        
        # 2. Mettre à jour les relations website_id
        logger.info("\n=== Étape 2: Mise à jour des relations ===")
        update_website_ids(conn)
        
        logger.info("\n✅ Traitement terminé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur générale : {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()