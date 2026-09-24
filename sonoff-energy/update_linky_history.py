import os
import csv
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

CSV_CLEAN_PATH = "/home/seb/sonoff-energy/historique_linky.csv"
CSV_BRUT_PATH = "/home/seb/sonoff-energy/historique_linky_brut.csv"

API_TOKEN = os.getenv('LINKY_API_TOKEN')
PDL = os.getenv('LINKY_PDL')

def validate_config():
    """Vérifie que la configuration est valide."""
    if not API_TOKEN or not PDL:
        raise ValueError("LINKY_API_TOKEN ou LINKY_PDL non configurés")

def load_existing_data(filepath):
    """Charge les données existantes dans un dictionnaire {YYYY-MM-DD: kwh}."""
    data = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        date_str, val_str = row[0].strip(), row[1].strip()
                        try:
                            data[date_str] = float(val_str)
                        except ValueError:
                            logger.warning(f"Valeur invalide: {val_str} pour {date_str}")
                            continue
        except Exception as e:
            logger.error(f"Erreur lecture {filepath}: {e}")
    return data

def process_brut_csv(filepath):
    """Extrait les données d'un export brut Enedis (Format DD/MM/YYYY;valeur;)."""
    brut_data = {}
    if not os.path.exists(filepath):
        logger.info(f"Fichier brut non trouvé: {filepath}")
        return brut_data

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(';')
                if len(parts) >= 2:
                    date_raw, val_raw = parts[0].strip(), parts[1].strip().replace(',', '.')
                    try:
                        dt = datetime.strptime(date_raw, "%d/%m/%Y")
                        date_iso = dt.strftime("%Y-%m-%d")
                        val_kwh = float(val_raw)
                        brut_data[date_iso] = val_kwh
                    except ValueError as e:
                        logger.warning(f"Erreur parsing brut: {line.strip()} - {e}")
                        continue
    except Exception as e:
        logger.error(f"Erreur lecture brut CSV: {e}")
    return brut_data

def fetch_api_range(start_date, end_date):
    """Interroge MyElectricalData pour une plage de dates avec retry."""
    headers = {"Authorization": API_TOKEN}

    for attempt, use_cache in enumerate([(False, "direct"), (True, "cache")]):
        try:
            cache_suffix = "/cache/" if use_cache[0] else ""
            url = f"https://www.myelectricaldata.fr/daily_consumption/{PDL}/start/{start_date}/end/{end_date}{cache_suffix}"

            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                logger.info(f"API {use_cache[1]} succès pour {start_date} à {end_date}")
                return parse_api_response(resp.json())
            else:
                logger.warning(f"API {use_cache[1]} status {resp.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Erreur API {use_cache[1]}: {e}")
            continue

    logger.error(f"Impossible de récupérer données API pour {start_date} à {end_date}")
    return {}

def parse_api_response(data):
    """Parse le JSON renvoyé par l'API MyElectricalData."""
    results = {}
    try:
        if isinstance(data, list):
            for item in data:
                if 'date' in item and 'value' in item:
                    val = float(item['value'])
                    val_kwh = val / 1000.0 if val > 100 else val
                    results[item['date']] = round(val_kwh, 2)
        elif isinstance(data, dict) and 'meter_reading' in data:
            intervals = data['meter_reading'].get('interval_reading', [])
            for item in intervals:
                if 'date' in item and 'value' in item:
                    val = float(item['value'])
                    val_kwh = val / 1000.0 if val > 100 else val
                    results[item['date']] = round(val_kwh, 2)
    except Exception as e:
        logger.error(f"Erreur parsing API: {e}")
    return results

def main():
    try:
        validate_config()
    except ValueError as e:
        logger.error(str(e))
        return

    logger.info("Chargement de l'historique local...")
    history = load_existing_data(CSV_CLEAN_PATH)
    initial_count = len(history)

    if history:
        last_date_str = max(history.keys())
        logger.info(f"Dernière date: {last_date_str}")
    else:
        last_date_str = "2023-01-01"
        logger.warning("Historique vide")

    logger.info("Traitement du fichier brut...")
    brut_data = process_brut_csv(CSV_BRUT_PATH)
    added_from_brut = 0
    for d, val in brut_data.items():
        if d not in history:
            history[d] = val
            added_from_brut += 1
    if added_from_brut > 0:
        logger.info(f"✅ {added_from_brut} lignes ajoutées depuis brut")

    last_dt = datetime.strptime(max(history.keys()), "%Y-%m-%d")
    today = datetime.now()

    if (today - last_dt).days > 1:
        start_str = (last_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        end_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"Interrogation API: {start_str} à {end_str}")

        api_data = fetch_api_range(start_str, end_str)
        added_from_api = 0
        for d, val in api_data.items():
            if d not in history:
                history[d] = val
                added_from_api += 1

        if added_from_api > 0:
            logger.info(f"✅ {added_from_api} lignes ajoutées depuis API")
        else:
            logger.warning("Aucune donnée nouvelle de l'API")

    sorted_history = sorted(history.items(), key=lambda x: x[0])
    with open(CSV_CLEAN_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for date_key, val in sorted_history:
            writer.writerow([date_key, f"{val:.2f}"])

    logger.info(f"✅ Total: {len(sorted_history)} records (+{len(sorted_history) - initial_count})")

if __name__ == "__main__":
    main()
