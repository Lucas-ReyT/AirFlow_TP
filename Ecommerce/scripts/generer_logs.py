import random
import sys
from datetime import datetime, timedelta

# --- Données réalistes d'une marketplace --

IPS = [
    "92.184.12.44", "185.220.101.12", "78.23.145.67", "213.95.11.88",
    "5.188.10.132", "91.108.4.15", "176.31.208.51", "62.210.114.199",
    "37.187.0.200", "82.66.14.25", "90.54.12.144", "51.15.201.77",
    "109.190.122.6", "212.47.234.67", "163.172.0.100",
]

# (method, url, status, size, weight)
URLS = [
    # Pages produits (trafic élevé)
    ("GET", "/produit/smartphone-samsung-galaxy-s24-ultra", 200, 48200, 10),
    ("GET", "/produit/laptop-dell-inspiron-15-amd", 200, 72100, 10),
    ("GET", "/produit/casque-audio-sony-wh1000xm5", 200, 38900, 9),
    ("GET", "/produit/aspirateur-dyson-v15", 200, 41000, 9),
    ("GET", "/produit/montre-connectee-apple-watch-9", 200, 55300, 9),

    # Pages catégories
    ("GET", "/categorie/informatique", 200, 22400, 8),
    ("GET", "/categorie/electromenager", 200, 19800, 7),
    ("GET", "/categorie/smartphones", 200, 25100, 8),

    # Pages panier / checkout (critique)
    ("GET", "/panier", 200, 8900, 6),
    ("POST", "/checkout/valider", 200, 3400, 5),
    ("POST", "/checkout/paiement", 200, 4100, 5),

    # Erreurs courantes (moins fréquentes)
    ("GET", "/produit/article-retire-de-vente", 404, 512, 1),
    ("GET", "/admin/dashboard", 403, 287, 1),
    ("GET", "/produit/inexistant-xyz", 404, 512, 1),
    ("POST", "/api/panier/ajouter", 500, 1024, 1),
    ("GET", "/api/stock/verifier", 503, 890, 1),

    # Assets statiques
    ("GET", "/static/css/main.min.css", 200, 18200, 6),
    ("GET", "/static/js/bundle.min.js", 200, 234100, 6),
    ("GET", "/static/img/logo.png", 200, 4200, 6),
    ("GET", "/favicon.ico", 200, 1150, 5),
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3) AppleWebKit/605.1.15 Mobile/15E148',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/121.0 Mobile',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'python-requests/2.31.0',  # Bot / scraper
    'Googlebot/2.1 (+http://www.google.com/bot.html)',
]

REFERRERS = [
    'https://www.google.fr/search?q=smartphone+pas+cher',
    'https://www.google.fr/shopping',
    'https://www.bing.com/search?q=laptop+dell',
    'https://www.lesnumeriques.com/',
    '-',  # Direct
    '-',
    '-',
]


def generer_log_line(date_str: str) -> str:
    """Génère une ligne de log Apache Combined Log Format."""

    ip = random.choice(IPS)

    methode, url, status, taille, _ = random.choices(
        URLS,
        weights=[u[4] for u in URLS],
        k=1
    )[0]

    user_agent = random.choice(USER_AGENTS)
    referrer = random.choice(REFERRERS)

    # Horodatage réaliste dans la journée (avec distribution plus naturelle)
    base = datetime.strptime(date_str, "%Y-%m-%d")

    hour = random.choices(
        range(24),
        weights=[1,1,1,1,2,3,5,8,10,12,15,18,20,22,25,22,20,18,15,10,6,4,2,1]
    )[0]

    delta = timedelta(
        hours=hour,
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )

    timestamp = (base + delta).strftime("%d/%b/%Y:%H:%M:%S +0200")

    # Format Apache Combined Log
    return (
        f'{ip} - - [{timestamp}] "{methode} {url} HTTP/1.1" '
        f'{status} {taille} "{referrer}" "{user_agent}"'
    )


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 generer_logs.py <date YYYY-MM-DD> <nb_lignes> <fichier_sortie>")
        sys.exit(1)

    date_str = sys.argv[1]

    try:
        nb_lignes = int(sys.argv[2])
    except ValueError:
        print("Erreur: nb_lignes doit être un entier")
        sys.exit(1)

    fichier_sortie = sys.argv[3]

    with open(fichier_sortie, "w", encoding="utf-8") as f:
        for _ in range(nb_lignes):
            f.write(generer_log_line(date_str) + "\n")

    print(f"[OK] {nb_lignes} lignes générées dans {fichier_sortie}")


if __name__ == "__main__":
    main()