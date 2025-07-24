import subprocess

# Liste des commandes à exécuter dans l’ordre
commands = [
    ("Scraping des documents", "python run_all_scrapers.py"),
    ("Conversion PDF → Word", "python convert_pdfs_to_word.py"),
    ("Ajout en base de données", "python add_word_documents.py"),
    ("Réorganisation de la base", "python reorganize_database.py"),
    ("Analyse intelligente", "python analyze_word_documents.py"),
    ("Vérification des résultats", "python check_pdfs.py"),
]

def run_pipeline():
    print("🚀 Démarrage du pipeline complet...\n")

    for step_name, command in commands:
        print(f"🔹 Étape : {step_name}")
        print(f"   ➤ Commande : {command}")

        try:
            result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
            print(f"✅ Succès : {step_name}")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'exécution de : {step_name}")
            print(e.stderr)
            break  # Stopper le pipeline en cas d'échec

        print("-" * 60)

    print("\n🎉 Pipeline terminé.")

if __name__ == "__main__":
    run_pipeline()
