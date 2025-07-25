import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(scraper_scrapedpdf);")
columns = cursor.fetchall()

print("\n📋 Colonnes dans scraper_scrapedpdf :")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()
