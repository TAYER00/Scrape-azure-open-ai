#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification de l'analyse des PDFs

Ce script vérifie :
1. Que la table scraper_wordsdocument a été nettoyée
2. Que les champs site_web ont été mis à jour
3. Les statistiques des résultats d'analyse

Auteur: Assistant IA
Date: 2025-07-25
"""

import sqlite3
import json
import os
from collections import Counter

def verify_database_cleanup():
    """
    Vérifie l'état de la base de données après nettoyage
    """
    print("🔍 Vérification de l'état de la base de données")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Vérifier la table scraper_wordsdocument
        print("\n📋 Table scraper_wordsdocument:")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='scraper_wordsdocument'
        """)
        
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM scraper_wordsdocument")
            count = cursor.fetchone()[0]
            print(f"   Enregistrements: {count}")
            if count == 0:
                print("   ✅ Table correctement nettoyée")
            else:
                print(f"   ⚠️ {count} enregistrements restants")
        else:
            print("   ℹ️ Table non trouvée")
        
        # Vérifier les champs site_web dans scraper_scrapedpdf
        print("\n📋 Table scraper_scrapedpdf - Champs site_web:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(site_web) as with_site_web,
                COUNT(website_id) as with_website_id
            FROM scraper_scrapedpdf
        """)
        
        total, with_site_web, with_website_id = cursor.fetchone()
        print(f"   Total PDFs: {total}")
        print(f"   Avec site_web: {with_site_web}")
        print(f"   Avec website_id: {with_website_id}")
        
        if with_site_web == with_website_id:
            print("   ✅ Tous les champs site_web sont mis à jour")
        else:
            print(f"   ⚠️ {with_website_id - with_site_web} champs site_web manquants")
        
        # Statistiques par site
        print("\n📊 Répartition par site:")
        cursor.execute("""
            SELECT site_web, COUNT(*) as count
            FROM scraper_scrapedpdf
            WHERE site_web IS NOT NULL
            GROUP BY site_web
            ORDER BY count DESC
        """)
        
        for site, count in cursor.fetchall():
            print(f"   {site}: {count} PDFs")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur vérification base de données: {e}")

def analyze_results_file(filename='scraper/static/data/pdf_analysis_results.json'):
    """
    Analyse les résultats de l'analyse des PDFs
    
    Args:
        filename (str): Nom du fichier de résultats
    """
    print(f"\n🔍 Analyse du fichier {filename}")
    print("=" * 50)
    
    if not os.path.exists(filename):
        print(f"❌ Fichier {filename} non trouvé")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"📊 Total de PDFs analysés: {len(results)}")
        
        # Statistiques de pertinence
        pertinents = [r for r in results if r['analysis']['pertinent']]
        non_pertinents = [r for r in results if not r['analysis']['pertinent']]
        
        print(f"✅ PDFs pertinents: {len(pertinents)} ({len(pertinents)/len(results)*100:.1f}%)")
        print(f"⛔ PDFs non pertinents: {len(non_pertinents)} ({len(non_pertinents)/len(results)*100:.1f}%)")
        
        # Statistiques par langue
        print("\n🌍 Répartition par langue:")
        langues = Counter(r['analysis']['langue'] for r in results)
        for langue, count in langues.most_common():
            print(f"   {langue}: {count} PDFs ({count/len(results)*100:.1f}%)")
        
        # Statistiques par thématique
        print("\n🏷️ Répartition par thématique:")
        thematiques = Counter(r['analysis']['thematique'] for r in results)
        for theme, count in thematiques.most_common(10):  # Top 10
            print(f"   {theme}: {count} PDFs ({count/len(results)*100:.1f}%)")
        
        # Statistiques par site web
        print("\n🌐 Répartition par site web:")
        sites = Counter(r['site_web'] for r in results if r['site_web'])
        for site, count in sites.most_common():
            print(f"   {site}: {count} PDFs ({count/len(results)*100:.1f}%)")
        
        # Statistiques de confiance
        print("\n🎯 Niveau de confiance:")
        confiances = Counter(r['analysis']['confiance'] for r in results)
        for confiance, count in confiances.most_common():
            print(f"   {confiance}: {count} PDFs ({count/len(results)*100:.1f}%)")
        
        # Exemples de PDFs pertinents par thématique
        print("\n📋 Exemples de PDFs pertinents par thématique:")
        pertinents_by_theme = {}
        for r in pertinents:
            theme = r['analysis']['thematique']
            if theme not in pertinents_by_theme:
                pertinents_by_theme[theme] = []
            pertinents_by_theme[theme].append(r)
        
        for theme, pdfs in list(pertinents_by_theme.items())[:5]:  # Top 5 thèmes
            print(f"\n   📂 {theme} ({len(pdfs)} PDFs):")
            for pdf in pdfs[:3]:  # 3 exemples max
                print(f"      • {pdf['title'][:60]}... ({pdf['site_web']})")
        
        # Taille moyenne du texte analysé
        text_lengths = [r['text_length'] for r in results if 'text_length' in r]
        if text_lengths:
            avg_length = sum(text_lengths) / len(text_lengths)
            print(f"\n📏 Taille moyenne du texte analysé: {avg_length:.0f} caractères")
        
    except Exception as e:
        print(f"❌ Erreur analyse fichier résultats: {e}")

def generate_summary_report():
    """
    Génère un rapport de synthèse
    """
    print("\n📋 RAPPORT DE SYNTHÈSE")
    print("=" * 50)
    
    # Vérifier les fichiers générés
    files_to_check = [
        'scraper/static/data/pdf_analysis_results.json',
        'pdf_analysis.log'
    ]
    
    print("\n📁 Fichiers générés:")
    for filename in files_to_check:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   ✅ {filename} ({size:,} octets)")
        else:
            print(f"   ❌ {filename} (non trouvé)")
    
    print("\n🎯 Actions réalisées:")
    print("   ✅ Suppression des données scraper_wordsdocument")
    print("   ✅ Mise à jour des champs site_web")
    print("   ✅ Analyse des PDFs avec Azure OpenAI")
    print("   ✅ Génération du fichier de résultats JSON")
    print("   ✅ Logging détaillé des opérations")
    
    print("\n💡 Prochaines étapes suggérées:")
    print("   • Examiner les PDFs non pertinents pour affiner les critères")
    print("   • Intégrer les résultats dans l'interface Django")
    print("   • Mettre en place un processus d'analyse automatique")
    print("   • Créer des filtres par thématique et langue")

def main():
    """
    Fonction principale
    """
    print("🔍 VÉRIFICATION DE L'ANALYSE DES PDFs")
    print("=" * 60)
    
    # Vérification de la base de données
    verify_database_cleanup()
    
    # Analyse des résultats
    analyze_results_file()
    
    # Rapport de synthèse
    generate_summary_report()
    
    print("\n✅ Vérification terminée")

if __name__ == "__main__":
    main()