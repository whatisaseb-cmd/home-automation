import ccxt
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Initialisation de l'instance Kraken
kraken = ccxt.kraken({
    'apiKey': os.getenv('API_KEY'),
    'secret': os.getenv('API_SECRET')
})

try:
    # Requête du solde
    solde = kraken.fetch_balance()
    euros = solde['total'].get('EUR', 0)
    print(f"✅ Connexion validée ! Solde disponible : {euros} €")
except Exception as e:
    print(f"❌ Échec de la connexion. Raison : {e}")
