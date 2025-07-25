#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper Intelligent

Ce script effectue un scraping intelligent en évitant de re-scraper
les fichiers déjà présents dans la base de données.

Auteur: Assistant IA
Date: 2025-01-27
"""

import os
import sys
import sqlite3
import subprocess
import time
import logging
from typing import Set, List, Dict
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntelligentScraper:
    """
    Scraper intelligent qui évite les doublons
    """
    
    def __init__(self):
        self.db_path = 'db.sqlite3'
        self.sites = {
            'agriculture.gov.ma': 'agriculture_scraper.py',
            'bkam.ma': 'bkam_scraper.py',
            'cese.ma': 'cese_scraper.py', 
            'finances.gov.ma': 'finances_scraper.py',
            'oecd.org': 'oecd_scraper.py'
        }
        
    def get_existing_files_from_db(self) -> Set[str]:
        """
        Récupère les fichiers déjà présents dans la base de données
        
        Returns:
            Set[str]: Ensemble des noms de fichiers déjà scrapés
        """
        try:
            if not os.path.exists(self.db_path):
                logger.info("📊 Base de données non trouvée - tous les fichiers seront scrapés")
                return set()
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT file_path 
                FROM scraper_scrapedpdf
            """)
            
            existing_files = set()
            for row in cursor.fetchall():
                file_path = row[0]
                filename = os.path.basename(file_path)
                existing_files.add(filename)
            
            conn.close()
            logger.info(f"📊 {len(existing_files)} fichiers déjà présents dans la base de données")
            return existing_files
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la lecture de la base de données: {e}")
            return set()
    
    def get_files_in_directory(self, directory: str) -> List[str]:
        """
        Récupère la liste des fichiers PDF dans un répertoire
        
        Args:
            directory (str): Chemin du répertoire
        
        Returns:
            List[str]: Liste des fichiers PDF
        """
        pdf_files = []
        
        if not os.path.exists(directory):
            return pdf_files
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(file)
            return pdf_files
        except Exception as e:
            logger.error(f"❌ Erreur lors de la lecture du répertoire {directory}: {e}")
            return pdf_files
    
    def check_scraping_needed(self, site: str) -> bool:
        """
        Vérifie si le scraping est nécessaire pour un site donné
        
        Args:
            site (str): Nom du site
        
        Returns:
            bool: True si scraping nécessaire
        """
        existing_files = self.get_existing_files_from_db()
        
        # Vérifier les fichiers dans le répertoire du site
        pdf_downloads_dir = os.path.join(site, 'pdf_downloads')
        current_files = set(self.get_files_in_directory(pdf_downloads_dir))
        
        # Fichiers qui ne sont pas encore en base
        new_files = current_files - existing_files
        
        if new_files:
            logger.info(f"🆕 {len(new_files)} nouveaux fichiers détectés pour {site}")
            for file in sorted(list(new_files)[:3]):  # Afficher max 3 exemples
                logger.info(f"   - {file}")
            if len(new_files) > 3:
                logger.info(f"   ... et {len(new_files) - 3} autres")
            return True
        else:
            logger.info(f"✅ Aucun nouveau fichier pour {site} - scraping ignoré")
            return False
    
    def run_scraper_for_site(self, site: str, scraper_script: str) -> bool:
        """
        Exécute le scraper pour un site spécifique
        
        Args:
            site (str): Nom du site
            scraper_script (str): Nom du script scraper
        
        Returns:
            bool: True si succès
        """
        try:
            # Chercher le script dans le répertoire du site
            script_path = os.path.join(site, scraper_script)
            
            if not os.path.exists(script_path):
                logger.warning(f"⚠️  Script {scraper_script} non trouvé pour {site}")
                return False
            
            logger.info(f"🚀 Démarrage du scraping pour {site}...")
            
            # Exécuter le scraper avec un timeout
            result = subprocess.run(
                ['python', script_path],
                cwd=site,  # Exécuter dans le répertoire du site
                check=True,
                capture_output=True,
                text=True,
                timeout=1200  # 20 minutes max par site
            )
            
            logger.info(f"✅ Scraping terminé avec succès pour {site}")
            
            # Afficher quelques lignes de sortie si disponibles
            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines[-3:]:  # Dernières 3 lignes
                    if line.strip():
                        logger.info(f"   {line}")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout du scraping pour {site} (>20 min)")
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur lors du scraping de {site}:")
            logger.error(f"   Code de retour: {e.returncode}")
            
            if e.stderr:
                logger.error(f"   Erreur: {e.stderr.strip()[:200]}...")  # Limiter la sortie
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors du scraping de {site}: {e}")
            return False
    
    def run_intelligent_scraping(self):
        """
        Exécute le scraping intelligent pour tous les sites
        """
        logger.info("\n" + "="*60)
        logger.info("🧠 SCRAPING INTELLIGENT - ÉVITEMENT DES DOUBLONS")
        logger.info("="*60)
        
        successful_sites = 0
        total_sites = len(self.sites)
        
        for site, scraper_script in self.sites.items():
            logger.info(f"\n🔍 Vérification du site: {site}")
            logger.info("-" * 40)
            
            # Vérifier si le scraping est nécessaire
            if self.check_scraping_needed(site):
                # Exécuter le scraper
                if self.run_scraper_for_site(site, scraper_script):
                    successful_sites += 1
                    logger.info(f"✅ Scraping réussi pour {site}")
                else:
                    logger.warning(f"⚠️  Scraping échoué pour {site}")
            else:
                # Pas de nouveau fichier, considérer comme succès
                successful_sites += 1
                logger.info(f"✅ Aucun scraping nécessaire pour {site}")
            
            # Petite pause entre les sites
            if site != list(self.sites.keys())[-1]:  # Pas de pause après le dernier site
                time.sleep(2)
        
        # Résumé
        logger.info("\n" + "="*60)
        logger.info("📊 RÉSUMÉ DU SCRAPING INTELLIGENT")
        logger.info("="*60)
        logger.info(f"✅ Sites traités avec succès: {successful_sites}/{total_sites}")
        
        if successful_sites == total_sites:
            logger.info("🎉 SCRAPING INTELLIGENT TERMINÉ AVEC SUCCÈS !")
            logger.info("   Tous les sites ont été traités intelligemment.")
        elif successful_sites > 0:
            logger.info("⚠️  SCRAPING PARTIELLEMENT RÉUSSI")
            logger.info(f"   {total_sites - successful_sites} site(s) ont échoué.")
        else:
            logger.info("❌ SCRAPING ÉCHOUÉ")
            logger.info("   Aucun site n'a pu être traité.")
        
        logger.info("="*60)
        
        return successful_sites > 0

def main():
    """
    Fonction principale
    """
    try:
        scraper = IntelligentScraper()
        success = scraper.run_intelligent_scraping()
        
        if success:
            logger.info("\n✅ Scraping intelligent terminé")
            sys.exit(0)
        else:
            logger.error("\n❌ Scraping intelligent échoué")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Scraping interrompu par l'utilisateur (Ctrl+C)")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"\n\n❌ ERREUR CRITIQUE DU SCRAPING INTELLIGENT !")
        logger.error(f"   Type: {type(e).__name__}")
        logger.error(f"   Message: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()