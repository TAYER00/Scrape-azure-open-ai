import sqlite3
import logging
from collections import defaultdict

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Connexion à la base de données SQLite"""
    return sqlite3.connect('db.sqlite3')

def verify_website_relations():
    """Vérifie les relations entre scraper_website et scraper_scrapedpdf"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Vérifier les sites web dans la table scraper_website
        logger.info("=== Sites web dans la base ===")
        cursor.execute("SELECT id, name, url FROM scraper_website ORDER BY name")
        websites = cursor.fetchall()
        
        for website_id, name, url in websites:
            logger.info(f"ID: {website_id} | Nom: {name} | URL: {url}")
        
        # 2. Statistiques par site web
        logger.info("\n=== Statistiques des PDFs par site ===")
        cursor.execute("""
            SELECT w.name, COUNT(p.id) as pdf_count
            FROM scraper_website w
            LEFT JOIN scraper_scrapedpdf p ON w.id = p.website_id
            GROUP BY w.id, w.name
            ORDER BY pdf_count DESC
        """)
        
        stats = cursor.fetchall()
        total_pdfs = 0
        
        for site_name, pdf_count in stats:
            logger.info(f"📊 {site_name}: {pdf_count} PDFs")
            total_pdfs += pdf_count
        
        logger.info(f"\n📈 Total PDFs: {total_pdfs}")
        
        # 3. Vérifier les PDFs sans website_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM scraper_scrapedpdf 
            WHERE website_id IS NULL
        """)
        
        orphan_count = cursor.fetchone()[0]
        logger.info(f"⚠️ PDFs sans website_id: {orphan_count}")
        
        if orphan_count > 0:
            logger.info("\n=== PDFs orphelins (sans website_id) ===")
            cursor.execute("""
                SELECT id, title, file_path 
                FROM scraper_scrapedpdf 
                WHERE website_id IS NULL
                LIMIT 10
            """)
            
            orphans = cursor.fetchall()
            for pdf_id, title, file_path in orphans:
                logger.warning(f"ID: {pdf_id} | Titre: {title[:50]}... | Chemin: {file_path[:80]}...")
        
        # 4. Exemples de PDFs avec relations correctes
        logger.info("\n=== Exemples de PDFs avec relations ===")
        cursor.execute("""
            SELECT w.name, p.title, p.file_path
            FROM scraper_scrapedpdf p
            JOIN scraper_website w ON p.website_id = w.id
            ORDER BY w.name, p.title
            LIMIT 15
        """)
        
        examples = cursor.fetchall()
        current_site = None
        
        for site_name, title, file_path in examples:
            if site_name != current_site:
                logger.info(f"\n🌐 {site_name}:")
                current_site = site_name
            logger.info(f"  📄 {title[:60]}...")
        
        # 5. Vérification de l'intégrité des données
        logger.info("\n=== Vérification de l'intégrité ===")
        
        # Vérifier les website_id invalides
        cursor.execute("""
            SELECT COUNT(*)
            FROM scraper_scrapedpdf p
            LEFT JOIN scraper_website w ON p.website_id = w.id
            WHERE p.website_id IS NOT NULL AND w.id IS NULL
        """)
        
        invalid_refs = cursor.fetchone()[0]
        if invalid_refs > 0:
            logger.error(f"❌ Références invalides détectées: {invalid_refs}")
        else:
            logger.info("✅ Toutes les références website_id sont valides")
        
        # Résumé final
        logger.info("\n=== RÉSUMÉ ===")
        logger.info(f"Sites web configurés: {len(websites)}")
        logger.info(f"PDFs avec relations: {total_pdfs - orphan_count}")
        logger.info(f"PDFs orphelins: {orphan_count}")
        logger.info(f"Références invalides: {invalid_refs}")
        
        if orphan_count == 0 and invalid_refs == 0:
            logger.info("🎉 Toutes les relations sont correctement configurées !")
        else:
            logger.warning("⚠️ Des problèmes de relations ont été détectés")
            
    except Exception as e:
        logger.error(f"Erreur lors de la vérification: {e}")
    finally:
        conn.close()

def main():
    logger.info("🔍 Vérification des relations website dans la base de données")
    verify_website_relations()

if __name__ == '__main__':
    main()