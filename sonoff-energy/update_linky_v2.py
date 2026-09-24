#!/usr/bin/env python3
"""
Update Linky history - NOW USES SQLITE DATABASE
Reads from API, writes to ~/data/maison.db instead of CSV
"""

import os
import sqlite3
import requests
from datetime import datetime, timedelta

# Configuration
DB_PATH = os.path.expanduser("~/data/maison.db")
API_TOKEN = os.getenv('LINKY_API_TOKEN', '')
PDL = os.getenv('LINKY_PDL', '')

def get_db_connection():
    """Connect to SQLite database"""
    return sqlite3.connect(DB_PATH)

def fetch_api_range(start_date, end_date):
    """Fetch data from MyElectricalData API"""
    if not API_TOKEN or not PDL:
        print("⚠️ Linky API credentials not configured")
        return {}

    headers = {"Authorization": API_TOKEN}
    url = f"https://www.myelectricaldata.fr/daily_consumption/{PDL}/start/{start_date}/end/{end_date}"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return parse_api_response(res.json())
    except Exception as e:
        print(f"⚠️ API error: {e}")

    return {}

def parse_api_response(data):
    """Parse JSON response"""
    results = {}
    if isinstance(data, list):
        for item in data:
            if 'date' in item and 'value' in item:
                val = float(item['value']) / 1000.0 if float(item['value']) > 100 else float(item['value'])
                results[item['date']] = round(val, 2)
    return results

def main():
    """Update Linky data from API to SQLite"""
    print("🔄 Updating Linky data from API...")

    db = get_db_connection()
    cursor = db.cursor()

    # Get last date in DB
    cursor.execute("SELECT MAX(date) FROM linky")
    last_date_row = cursor.fetchone()
    last_date_str = last_date_row[0] if last_date_row[0] else "2023-01-01"

    print(f"📅 Last record: {last_date_str}")

    # Fetch new data from API
    last_dt = datetime.strptime(last_date_str, "%Y-%m-%d")
    today = datetime.now()

    if (today - last_dt).days > 1:
        start_str = (last_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        end_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        print(f"🌐 Fetching API data from {start_str} to {end_str}...")
        api_data = fetch_api_range(start_str, end_str)

        added = 0
        for date_key, kwh_val in api_data.items():
            cost = round(kwh_val * 0.19 + 0.63, 2)  # Approximate tariff
            try:
                cursor.execute("INSERT OR REPLACE INTO linky (date, kwh, cost) VALUES (?, ?, ?)",
                             (date_key, kwh_val, cost))
                added += 1
            except Exception as e:
                print(f"❌ Error inserting {date_key}: {e}")

        if added > 0:
            db.commit()
            print(f"✅ {added} new records added to database")
        else:
            print("⚠️ No new data from API")
    else:
        print("ℹ️ Data is current")

    # Get total count
    cursor.execute("SELECT COUNT(*) FROM linky")
    total = cursor.fetchone()[0]
    print(f"📊 Total records in DB: {total}")

    db.close()

if __name__ == "__main__":
    main()
