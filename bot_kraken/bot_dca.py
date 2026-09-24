import ccxt
import os
import datetime
import logging
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

MONTANT_BULL = 12
MONTANT_BEAR = 6

def validate_env_vars():
    """Vérifie que toutes les variables d'environnement requises sont définies."""
    required = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'API_KEY', 'API_SECRET']
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        logger.error(f"Variables d'env manquantes: {', '.join(missing)}")
        raise ValueError(f"Missing env vars: {missing}")

def envoyer_telegram(message):
    """Envoie un message Telegram avec gestion d'erreur."""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        logger.warning("Telegram non configuré")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        logger.info("Message Telegram envoyé")
    except requests.RequestException as e:
        logger.error(f"Erreur Telegram: {e}")

def analyser_tendance(kraken, symbole):
    """Analyse la tendance du marché avec SMA 200 correct."""
    try:
        ohlcv = kraken.fetch_ohlcv(symbole, timeframe='1d', limit=200)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # SMA 200 correct (rolling mean)
        sma_200 = df['close'].rolling(window=200).mean().iloc[-1]
        prix_actuel = df['close'].iloc[-1]

        if pd.isna(sma_200):
            logger.warning("SMA 200 ne peut pas être calculée (données insuffisantes)")
            return None, None, None, "ERREUR"

        est_haussier = prix_actuel > sma_200
        tendance_txt = "HAUSSIÈRE 🚀" if est_haussier else "BAISSIÈRE 📉"

        return est_haussier, prix_actuel, sma_200, tendance_txt
    except Exception as e:
        logger.error(f"Erreur analyse: {e}")
        return None, None, None, "ERREUR"

def executer_achat_smart_dca():
    """Exécute l'achat DCA intelligent."""
    try:
        validate_env_vars()
    except ValueError as e:
        logger.error(str(e))
        return

    symbole = 'BTC/EUR'
    try:
        kraken = ccxt.kraken({
            'apiKey': os.getenv('API_KEY'),
            'secret': os.getenv('API_SECRET'),
            'enableRateLimit': True,
        })
    except Exception as e:
        logger.error(f"Erreur connexion Kraken: {e}")
        envoyer_telegram(f"❌ Erreur connexion Kraken: {e}")
        return

    maintenant = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    est_haussier, prix, sma, tendance = analyser_tendance(kraken, symbole)

    if est_haussier is None:
        msg = "❌ Impossible de récupérer la tendance. Achat annulé par sécurité."
        logger.warning(msg)
        envoyer_telegram(msg)
        return

    montant_a_investir = MONTANT_BULL if est_haussier else MONTANT_BEAR

    if montant_a_investir <= 0:
        msg = f"⏸ *DCA en pause*\nTendance : {tendance}\nPrix : {prix:.2f}€ | SMA200 : {sma:.2f}€"
        logger.info(msg)
        envoyer_telegram(msg)
        return

    try:
        volume_btc = montant_a_investir / prix
        ordre = kraken.create_market_buy_order(symbole, volume_btc)

        msg_succes = (
            f"🤖 *Smart DCA Exécuté*\n"
            f"Tendance : {tendance}\n"
            f"Achat : {volume_btc:.6f} BTC\n"
            f"Prix : {prix:.2f} € | SMA200 : {sma:.2f} €\n"
            f"Investi : {montant_a_investir} €"
        )
        logger.info(msg_succes)
        envoyer_telegram(msg_succes)

    except ccxt.InsufficientFunds:
        msg = f"⚠️ Fonds insuffisants pour investir {montant_a_investir}€."
        logger.warning(msg)
        envoyer_telegram(msg)
    except ccxt.ExchangeError as e:
        msg = f"❌ Erreur Kraken: {e}"
        logger.error(msg)
        envoyer_telegram(msg)
    except Exception as e:
        msg = f"❌ Erreur achat: {e}"
        logger.error(msg)
        envoyer_telegram(msg)

if __name__ == "__main__":
    executer_achat_smart_dca()
