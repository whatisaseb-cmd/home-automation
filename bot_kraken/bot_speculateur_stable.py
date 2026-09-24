import ccxt
import os
import pandas as pd
import requests
import datetime
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = "/home/seb/bot_kraken"
TRADE_LOG = os.path.join(LOG_DIR, "trades.csv")

def envoyer_telegram(message):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def log_mouvement(nature, montant_usdc, prix):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    ligne = f"{date_str},{nature},{montant_usdc:.2f},{prix:.2f}\n"
    with open(TRADE_LOG, "a") as f:
        f.write(ligne)

def piloter_speculation_usdc():
    symbole = 'BTC/USDC' # Changé en USDC
    mise_depart = float(os.getenv('INVESTISSEMENT_INITIAL', 0))
    
    kraken = ccxt.kraken({
        'apiKey': os.getenv('API_KEY'),
        'secret': os.getenv('API_SECRET'),
        'enableRateLimit': True,
    })

    # 1. Analyse Tendance SMA 200
    ohlcv = kraken.fetch_ohlcv(symbole, timeframe='1d', limit=200)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    sma_200 = df['close'].mean()
    prix_actuel = df['close'].iloc[-1]
    est_haussier = prix_actuel > sma_200

    # 2. Portefeuille
    solde = kraken.fetch_balance()
    usdc_dispo = solde['total'].get('USDC', 0) # Changé en USDC
    btc_dispo = solde['total'].get('BTC', 0)
    valeur_totale_usdc = usdc_dispo + (btc_dispo * prix_actuel)

    # 3. Performance
    gain_absolu = valeur_totale_usdc - mise_depart
    perf = (gain_absolu / mise_depart) * 100 if mise_depart > 0 else 0

    # 4. Décision
    if est_haussier and usdc_dispo > 10:
        montant_achat = usdc_dispo * 0.98
        kraken.create_market_buy_order(symbole, montant_achat / prix_actuel)
        log_mouvement("ACHAT (SMA200+)", montant_achat, prix_actuel)
        envoyer_telegram(f"🚀 *Achat Spéculatif BTC*\nInvestissement : {montant_achat:.2f} USDC.")
        
    elif not est_haussier and btc_dispo * prix_actuel > 10:
        valeur_vente = btc_dispo * prix_actuel
        kraken.create_market_sell_order(symbole, btc_dispo)
        log_mouvement("VENTE (SMA200-)", valeur_vente, prix_actuel)
        envoyer_telegram(f"🛡️ *Protection Capital*\nVente BTC pour retour en USDC.")

if __name__ == "__main__":
    piloter_speculation_usdc()
