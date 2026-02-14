import sqlite3
import matplotlib.pyplot as plt
import os

# ==============================
# PATH CONFIG
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "nids.db")

# ==============================
# CONNECT TO DATABASE
# ==============================
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# ==============================
# ATTACK TYPE DISTRIBUTION
# ==============================
cursor.execute("""
    SELECT threat_type, COUNT(*) 
    FROM alerts 
    GROUP BY threat_type
""")
attack_data = cursor.fetchall()

if attack_data:
    labels = [row[0] for row in attack_data]
    counts = [row[1] for row in attack_data]

    plt.figure()
    plt.pie(counts, labels=labels, autopct='%1.1f%%')
    plt.title("Attack Type Distribution")
    plt.show()
else:
    print("No attack data found.")

# ==============================
# ATTACKS BY COUNTRY
# ==============================
cursor.execute("""
    SELECT country, COUNT(*) 
    FROM alerts 
    GROUP BY country
""")
country_data = cursor.fetchall()

if country_data:
    countries = [row[0] for row in country_data]
    counts = [row[1] for row in country_data]

    plt.figure()
    plt.bar(countries, counts)
    plt.title("Attacks by Country")
    plt.xticks(rotation=45)
    plt.show()

conn.close()
