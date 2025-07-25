#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Intelligent de Traitement PDF

Ce script automatise le processus complet de traitement des PDFs :
1. Scraping intelligent (évite les doublons)
2. Insertion intelligente en base de données
3. Analyse OpenAI des PDFs non analysés
4. Démarrage automatique du serveur Django

Auteur: Assistant IA
Date: 2025-01-27
"""

import os
import sys
import subprocess
import time
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligent_pipeline.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class IntelligentPipeline:
    """
    Pipeline intelligent pour le traitement automatisé des PDFs
    """
    
    def __init__(self):
        self.db_path = 'db.sqlite3'
        self.result_file = 'scraper/static/data/pdf_analysis_results.json'
        self.sites = [
            'agriculture.gov.ma',
            'bkam.ma', 
            'cese.ma',
            'finances.gov.ma',
            'oecd.org'
        ]
        
    def print_header(self):
        """Affiche l'en-tête du pipeline"""
        print("\n" + "="*60)
        print("🚀 PIPELINE INTELLIGENT DE TRAITEMENT PDF")
        print("="*60)
        print("📋 Fonctionnalités intelligentes :")
        print("   🧠 Scraping intelligent (évite les doublons)")
        print("   🧠 Insertion intelligente en base de données")
        print("   🧠 Analyse OpenAI des PDFs non analysés uniquement")
        print("   🧠 Démarrage automatique du serveur Django")
        print("="*60)
        
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
    
    def get_analyzed_pdfs(self) -> Set[int]:
        """
        Récupère les IDs des PDFs déjà analysés
        
        Returns:
            Set[int]: Ensemble des IDs des PDFs déjà analysés
        """
        try:
            if not os.path.exists(self.result_file):
                logger.info("📊 Aucun fichier de résultats d'analyse trouvé - tous les PDFs seront analysés")
                return set()
                
            with open(self.result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            analyzed_ids = {result['id'] for result in results}
            logger.info(f"📊 {len(analyzed_ids)} PDFs déjà analysés")
            return analyzed_ids
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la lecture des résultats d'analyse: {e}")
            return set()
    
    def check_files_in_directory(self, directory: str) -> List[str]:
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
    
    def check_scraping_needed(self) -> bool:
        """
        Vérifie si le scraping est nécessaire
        
        Returns:
            bool: True si scraping nécessaire
        """
        logger.info("\n🔍 VÉRIFICATION DE LA NÉCESSITÉ DU SCRAPING")
        logger.info("-" * 50)
        
        existing_files = self.get_existing_files_from_db()
        new_files_found = False
        
        for site in self.sites:
            pdf_downloads_dir = os.path.join(site, 'pdf_downloads')
            current_files = set(self.check_files_in_directory(pdf_downloads_dir))
            
            # Fichiers qui ne sont pas encore en base
            new_files = current_files - existing_files
            
            if new_files:
                logger.info(f"🆕 {len(new_files)} nouveaux fichiers détectés pour {site}")
                for file in sorted(list(new_files)[:3]):  # Afficher max 3 exemples
                    logger.info(f"   - {file}")
                if len(new_files) > 3:
                    logger.info(f"   ... et {len(new_files) - 3} autres")
                new_files_found = True
            else:
                logger.info(f"✅ Aucun nouveau fichier pour {site}")
        
        return new_files_found
    
    def check_analysis_needed(self) -> bool:
        """
        Vérifie si l'analyse est nécessaire
        
        Returns:
            bool: True si analyse nécessaire
        """
        logger.info("\n🔍 VÉRIFICATION DE LA NÉCESSITÉ DE L'ANALYSE")
        logger.info("-" * 50)
        
        try:
            if not os.path.exists(self.db_path):
                logger.info("📊 Base de données non trouvée - analyse non nécessaire")
                return False
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Compter le total de PDFs en base
            cursor.execute("SELECT COUNT(*) FROM scraper_scrapedpdf")
            total_pdfs = cursor.fetchone()[0]
            
            conn.close()
            
            # Compter les PDFs déjà analysés
            analyzed_pdfs = self.get_analyzed_pdfs()
            
            unanalyzed_count = total_pdfs - len(analyzed_pdfs)
            
            logger.info(f"📊 PDFs en base de données: {total_pdfs}")
            logger.info(f"📊 PDFs déjà analysés: {len(analyzed_pdfs)}")
            logger.info(f"📊 PDFs à analyser: {unanalyzed_count}")
            
            return unanalyzed_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification de l'analyse: {e}")
            return False
    
    def run_intelligent_scraping(self) -> bool:
        """
        Exécute le scraping intelligent
        
        Returns:
            bool: True si succès
        """
        logger.info("\n" + "="*50)
        logger.info("🔄 ÉTAPE 1: SCRAPING INTELLIGENT")
        logger.info("="*50)
        
        if not self.check_scraping_needed():
            logger.info("✅ Aucun nouveau fichier détecté - scraping ignoré")
            return True
        
        try:
            logger.info("🚀 Démarrage du scraping intelligent...")
            
            result = subprocess.run(
                ['python', 'intelligent_scraper.py'],
                check=True,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes max
            )
            
            logger.info("✅ Scraping intelligent terminé avec succès")
            
            # Afficher la sortie si elle existe
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[-10:]:  # Dernières 10 lignes
                    logger.info(f"   {line}")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout du scraping intelligent (>30 min)")
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur lors du scraping intelligent:")
            logger.error(f"   Code de retour: {e.returncode}")
            
            if e.stderr:
                logger.error(f"   Erreur: {e.stderr.strip()}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors du scraping: {e}")
            return False
    
    def run_database_reorganization(self) -> bool:
        """
        Exécute la réorganisation de la base de données
        
        Returns:
            bool: True si succès
        """
        logger.info("\n" + "="*50)
        logger.info("🔄 ÉTAPE 2: RÉORGANISATION DE LA BASE DE DONNÉES")
        logger.info("="*50)
        
        try:
            logger.info("🚀 Démarrage de la réorganisation de la base de données...")
            
            result = subprocess.run(
                ['python', 'reorganize_database.py'],
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            logger.info("✅ Réorganisation de la base de données terminée avec succès")
            
            # Afficher la sortie si elle existe
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[-5:]:  # Dernières 5 lignes
                    logger.info(f"   {line}")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout de la réorganisation (>5 min)")
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur lors de la réorganisation:")
            logger.error(f"   Code de retour: {e.returncode}")
            
            if e.stderr:
                logger.error(f"   Erreur: {e.stderr.strip()}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de la réorganisation: {e}")
            return False
    
    def run_intelligent_analysis(self) -> bool:
        """
        Exécute l'analyse intelligente des PDFs
        
        Returns:
            bool: True si succès
        """
        logger.info("\n" + "="*50)
        logger.info("🔄 ÉTAPE 3: ANALYSE INTELLIGENTE DES PDFs")
        logger.info("="*50)
        
        if not self.check_analysis_needed():
            logger.info("✅ Aucun nouveau PDF à analyser - analyse ignorée")
            return True
        
        try:
            logger.info("🚀 Démarrage de l'analyse intelligente des PDFs...")
            
            # Utiliser le mode only_new pour ne traiter que les nouveaux PDFs
            result = subprocess.run(
                ['python', '-c', 
                 'import analyze_pdfs_from_database; analyze_pdfs_from_database.main(only_new=True, skip_cleanup=True)'],
                check=True,
                capture_output=True,
                text=True,
                timeout=3600  # 60 minutes max
            )
            
            logger.info("✅ Analyse intelligente des PDFs terminée avec succès")
            
            # Afficher la sortie si elle existe
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[-10:]:  # Dernières 10 lignes
                    logger.info(f"   {line}")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout de l'analyse (>60 min)")
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur lors de l'analyse:")
            logger.error(f"   Code de retour: {e.returncode}")
            
            if e.stderr:
                logger.error(f"   Erreur: {e.stderr.strip()}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de l'analyse: {e}")
            return False
    
    def start_django_server(self) -> bool:
        """
        Démarre le serveur Django
        
        Returns:
            bool: True si succès
        """
        logger.info("\n" + "="*50)
        logger.info("🔄 ÉTAPE 4: DÉMARRAGE DU SERVEUR DJANGO")
        logger.info("="*50)
        
        try:
            logger.info("🚀 Démarrage du serveur Django...")
            
            # Démarrer le serveur en arrière-plan
            process = subprocess.Popen(
                ['python', 'manage.py', 'runserver'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Attendre un peu pour vérifier que le serveur démarre
            time.sleep(3)
            
            if process.poll() is None:
                logger.info("✅ Serveur Django démarré avec succès !")
                logger.info("🌐 Le serveur est maintenant actif.")
                logger.info("🔗 Vous pouvez accéder à l'interface à : http://127.0.0.1:8000/")
                logger.info("⚠️  Utilisez Ctrl+C pour arrêter le serveur.")
                
                # Attendre que l'utilisateur arrête le serveur
                try:
                    process.wait()
                except KeyboardInterrupt:
                    logger.info("\n⏹️  Arrêt du serveur Django demandé par l'utilisateur...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    logger.info("✅ Serveur Django arrêté")
                
                return True
            else:
                logger.error("❌ Le serveur Django n'a pas pu démarrer")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du serveur Django: {e}")
            return False
    
    def run_pipeline(self):
        """
        Exécute le pipeline complet
        """
        self.print_header()
        
        start_time = datetime.now()
        steps_completed = 0
        total_steps = 4
        
        try:
            # Étape 1: Scraping intelligent
            if self.run_intelligent_scraping():
                steps_completed += 1
                logger.info("✅ Étape 1 terminée avec succès")
            else:
                logger.warning("⚠️  Étape 1 échouée, mais continuation du pipeline...")
            
            time.sleep(2)  # Pause entre les étapes
            
            # Étape 2: Réorganisation de la base de données
            if self.run_database_reorganization():
                steps_completed += 1
                logger.info("✅ Étape 2 terminée avec succès")
            else:
                logger.warning("⚠️  Étape 2 échouée, mais continuation du pipeline...")
            
            time.sleep(2)  # Pause entre les étapes
            
            # Étape 3: Analyse intelligente
            if self.run_intelligent_analysis():
                steps_completed += 1
                logger.info("✅ Étape 3 terminée avec succès")
            else:
                logger.warning("⚠️  Étape 3 échouée, mais continuation du pipeline...")
            
            time.sleep(2)  # Pause entre les étapes
            
            # Étape 4: Démarrage du serveur Django
            if self.start_django_server():
                steps_completed += 1
                logger.info("✅ Étape 4 terminée avec succès")
            else:
                logger.error("❌ Étape 4 échouée")
            
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Pipeline interrompu par l'utilisateur (Ctrl+C)")
        
        except Exception as e:
            logger.error(f"\n\n❌ ERREUR CRITIQUE DU PIPELINE !")
            logger.error(f"   Type: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
        
        finally:
            # Résumé final
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("\n" + "="*60)
            logger.info("📊 RÉSUMÉ DU PIPELINE INTELLIGENT")
            logger.info("="*60)
            logger.info(f"✅ Étapes réussies : {steps_completed}/{total_steps}")
            logger.info(f"⏰ Durée totale : {duration}")
            
            if steps_completed == total_steps:
                logger.info("🎉 PIPELINE TERMINÉ AVEC SUCCÈS !")
                logger.info("   Tous les traitements ont été effectués intelligemment.")
            elif steps_completed >= 2:
                logger.info("⚠️  PIPELINE PARTIELLEMENT RÉUSSI")
                logger.info(f"   {total_steps - steps_completed} étape(s) ont échoué.")
            else:
                logger.info("❌ PIPELINE ÉCHOUÉ")
                logger.info("   La plupart des étapes ont échoué.")
            
            logger.info(f"\n⏰ Pipeline terminé à {end_time.strftime('%H:%M:%S')}")
            logger.info("="*60)

def main():
    """
    Fonction principale
    """
    pipeline = IntelligentPipeline()
    pipeline.run_pipeline()

if __name__ == '__main__':
    main()
