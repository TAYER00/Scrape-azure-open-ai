import os
from pdf2docx import Converter

def convert_pdfs_to_word(pdf_folder, word_folder):
    """Convertit tous les PDFs d'un dossier en fichiers Word (.docx)"""
    if not os.path.exists(word_folder):
        os.makedirs(word_folder)
        print(f"📁 Dossier créé : {word_folder}")

    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"⚠️  Aucun fichier PDF trouvé dans : {pdf_folder}")
        return
    
    print(f"📄 {len(pdf_files)} fichier(s) PDF trouvé(s) dans : {pdf_folder}")
    print("-" * 60)

    for i, filename in enumerate(pdf_files, 1):
        pdf_path = os.path.join(pdf_folder, filename)
        word_filename = os.path.splitext(filename)[0] + ".docx"
        word_path = os.path.join(word_folder, word_filename)

        try:
            print(f"[{i}/{len(pdf_files)}] Conversion de : {filename}")
            cv = Converter(pdf_path)
            cv.convert(word_path, start=0, end=None)
            cv.close()
            print(f"✅ Converti en : {word_filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la conversion de {filename} : {e}")
        print()

def main():
    """Fonction principale pour convertir les PDFs de tous les dossiers spécifiés"""
    print("🔄 Début de la conversion PDF vers Word")
    print("=" * 60)
    
    # Dossiers à traiter
    folders = [
        {
            "pdf": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\finances.gov.ma\pdf_downloads",
            "word": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\finances.gov.ma\words_downloads"
        },
        {
            "pdf": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\cese.ma\pdf_downloads",
            "word": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\cese.ma\words_downloads"
        },
        {
            "pdf": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\agriculture.gov.ma\pdf_downloads",
            "word": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\agriculture.gov.ma\words_downloads"
        },
        {
            "pdf": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\oecd.org\pdf_downloads",
            "word": r"C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\oecd.org\words_downloads"
        },
        {
            "pdf": r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\bkam.ma\bkam.ma\pdf_downloads\Communiques\pdf_scraper',
            "word": r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\bkam.ma\bkam.ma\pdf_downloads\Communiques\words_downloads',
        },

        {
            "pdf": r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\bkam.ma\bkam.ma\pdf_downloads\Discours\pdf_scraper',
            "word": r'C:\Users\anouar\Downloads\Scraping-web-sites-auto-naviguation\Scraping-web-sites-auto-naviguation-master\bkam.ma\bkam.ma\pdf_downloads\Discours\words_downloads',
        }


    ]
    
    total_folders = len(folders)
    
    for i, folder in enumerate(folders, 1):
        site_name = os.path.basename(os.path.dirname(folder["pdf"]))
        print(f"\n🌐 [{i}/{total_folders}] Traitement du site : {site_name}")
        
        if not os.path.exists(folder["pdf"]):
            print(f"⚠️  Dossier PDF non trouvé : {folder['pdf']}")
            continue
            
        convert_pdfs_to_word(folder["pdf"], folder["word"])
    
    print("\n" + "=" * 60)
    print("🎉 Conversion terminée !")

if __name__ == "__main__":
    main()