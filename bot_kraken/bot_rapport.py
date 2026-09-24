import ccxt
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def envoyer_telegram(message):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def envoyer_rapport_quotidien():
    kraken = ccxt.kraken({
        'apiKey': os.getenv('API_KEY'),
        'secret': os.getenv('API_SECRET'),
    })
    
    try:
        solde = kraken.fetch_balance()
        btc_total = solde['total'].get('BTC', 0)
        eur_dispo = solde['total'].get('EUR', 0)
        
        ticker = kraken.fetch_ticker('BTC/EUR')
        prix_actuel = ticker['last']
        valeur_portefeuille = btc_total * prix_actuel
        
        trades = kraken.fetch_my_trades('BTC/EUR')
        total_paye = sum(t['cost'] for t in trades)
        total_btc_achete = sum(t['amount'] for t in trades)
        prm = total_paye / total_btc_achete if total_btc_achete > 0 else 0
        
        performance = ((prix_actuel - prm) / prm * 100) if prm > 0 else 0
        
        rapport = (
            f"📊 *État des lieux quotidien*\n\n"
            f"💰 *Solde BTC :* {btc_total:.6f} BTC\n"
            f"💶 *Valeur actuelle :* {valeur_portefeuille:.2f} €\n"
            f"📉 *Prix de revient moyen :* {prm:.2f} €\n"
            f"🚀 *Performance :* {performance:+.2f}%\n\n"
            f"💳 *Euros disponibles :* {eur_dispo:.2f} €"
        )
        envoyer_telegram(rapport)
        print("Rapport envoyé avec succès sur Telegram.")
        
    except Exception as e:
        msg_erreur = f"❌ Erreur lors du rapport : {e}"
        print(msg_erreur)
        envoyer_telegram(msg_erreur)

if __name__ == "__main__":
    envoyer_rapport_quotidien()
