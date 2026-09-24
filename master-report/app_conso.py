#!/usr/bin/env python3
"""
Energy Consumption Dashboard - SQLite Version
Reads from ~/data/maison.db for Linky (electricity) and Gas data
"""

import os
import csv
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, send_file, jsonify

app = Flask(__name__)

# Paths
BASE_DIR = '/home/seb/sonoff-energy'
DB_PATH = os.path.expanduser('~/data/maison.db')
CAR_CSV = os.path.join(BASE_DIR, 'conso_manuelle.csv')
GAS_BACKUP_CSV = os.path.join(BASE_DIR, 'conso_gaz.csv')

def get_db_connection():
    """Connect to SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def load_linky_data():
    """Load electricity data from SQLite"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT date, kwh, cost FROM linky ORDER BY date DESC LIMIT 365")
        rows = cursor.fetchall()
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in rows]
        conn.close()
        return data
    except Exception as e:
        print(f"❌ Error loading Linky: {e}")
        conn.close()
        return []

def load_gas_data():
    """Load gas data from SQLite"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT date, kwh, cost FROM gas ORDER BY date DESC LIMIT 365")
        rows = cursor.fetchall()
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in rows]
        conn.close()
        return data
    except Exception as e:
        print(f"❌ Error loading Gas: {e}")
        conn.close()
        return []

def load_car_data():
    """Load EV charging data from SQLite"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT date, kwh, cost FROM car ORDER BY date DESC LIMIT 365")
        rows = cursor.fetchall()
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in rows]
        conn.close()
        return data
    except Exception as e:
        print(f"❌ Error loading Car: {e}")
        conn.close()
        return []

def load_manual_csv(filepath):
    """Load manual entries from CSV backup"""
    entries = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        try:
                            d_str = row[0].strip()
                            v_num = float(row[1].strip().replace(',', '.'))
                            entries.append({'date': d_str, 'val': v_num})
                        except ValueError:
                            continue
        except Exception as e:
            print(f"⚠️ Error loading manual CSV: {e}")

    entries.sort(key=lambda x: x['date'], reverse=True)
    return entries

def save_manual_entry(filepath, date_str, val):
    """Add or update manual entry"""
    entries = load_manual_csv(filepath)
    entries = [e for e in entries if e['date'] != date_str]
    entries.append({'date': date_str, 'val': float(val)})
    entries.sort(key=lambda x: x['date'], reverse=True)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for e in entries:
                writer.writerow([e['date'], f"{e['val']:.2f}"])
    except Exception as e:
        print(f"❌ Error saving entry: {e}")

def delete_manual_entry(filepath, date_str):
    """Delete manual entry"""
    entries = load_manual_csv(filepath)
    entries = [e for e in entries if e['date'] != date_str]
    entries.sort(key=lambda x: x['date'], reverse=True)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for e in entries:
                writer.writerow([e['date'], f"{e['val']:.2f}"])
    except Exception as e:
        print(f"❌ Error deleting entry: {e}")

@app.route('/')
def index():
    """Main dashboard page"""
    linky_data = load_linky_data()
    gas_data = load_gas_data()
    car_data = load_car_data()
    manual_data = load_manual_csv(CAR_CSV)

    # Calculate stats
    linky_total = sum(d['val'] for d in linky_data) if linky_data else 0
    linky_cost = sum(d['cost'] for d in linky_data) if linky_data else 0
    gas_total = sum(d['val'] for d in gas_data) if gas_data else 0
    gas_cost = sum(d['cost'] for d in gas_data) if gas_data else 0
    car_total = sum(d['val'] for d in car_data) if car_data else 0
    car_cost = sum(d['cost'] for d in car_data) if car_data else 0

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consommation Maison</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                transition: transform 0.3s, box-shadow 0.3s;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(0,0,0,0.15);
            }
            .card-title {
                font-size: 1.3em;
                font-weight: 600;
                margin-bottom: 15px;
                color: #333;
            }
            .stat {
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            .stat-label {
                color: #666;
            }
            .stat-value {
                font-weight: 600;
                color: #333;
            }
            .table-container {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            th {
                background: #f8f9fa;
                font-weight: 600;
                color: #333;
            }
            tr:hover {
                background: #f8f9fa;
            }
            .badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 500;
            }
            .badge-electric {
                background: #e3f2fd;
                color: #1976d2;
            }
            .badge-gas {
                background: #fff3e0;
                color: #f57c00;
            }
            .badge-car {
                background: #e8f5e9;
                color: #388e3c;
            }
            .form-group {
                margin-bottom: 15px;
            }
            input, button {
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #ddd;
                font-size: 1em;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                cursor: pointer;
                font-weight: 600;
            }
            button:hover {
                background: #5568d3;
            }
            .source-badge {
                font-size: 0.75em;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Consommation Maison</h1>
                <p>Tableau de bord énergie - Données temps réel SQLite</p>
                <p style="font-size: 0.9em; margin-top: 10px;">Mis à jour: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-title">⚡ Électricité</div>
                    <div class="stat">
                        <span class="stat-label">Total (kWh)</span>
                        <span class="stat-value">""" + f"{linky_total:.2f}" + """</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Coût (€)</span>
                        <span class="stat-value">""" + f"{linky_cost:.2f}" + """</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Enregistrements</span>
                        <span class="stat-value">""" + str(len(linky_data)) + """</span>
                    </div>
                    <span class="source-badge badge badge-electric">SQLite</span>
                </div>

                <div class="card">
                    <div class="card-title">🔥 Gaz</div>
                    <div class="stat">
                        <span class="stat-label">Total (kWh)</span>
                        <span class="stat-value">""" + f"{gas_total:.2f}" + """</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Coût (€)</span>
                        <span class="stat-value">""" + f"{gas_cost:.2f}" + """</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Enregistrements</span>
                        <span class="stat-value">""" + str(len(gas_data)) + """</span>
                    </div>
                    <span class="source-badge badge badge-gas">SQLite</span>
                </div>

                <div class="card">
                    <div class="card-title">🔋 Voiture (EV)</div>
                    <div class="stat">
                        <span class="stat-label">Total (kWh)</span>
                        <span class="stat-value">""" + f"{car_total:.2f}" + """</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Coût (€)</span>
                        <span class="stat-value">""" + f"{car_cost:.2f}" + """</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Enregistrements</span>
                        <span class="stat-value">""" + str(len(car_data)) + """</span>
                    </div>
                    <span class="source-badge badge badge-car">SQLite</span>
                </div>
            </div>

            <div class="table-container">
                <h2 style="margin-bottom: 20px;">📈 Données Récentes</h2>

                <h3 style="margin-top: 20px; margin-bottom: 10px;">⚡ Électricité (Linky) - Derniers 10 jours</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Consommation (kWh)</th>
                            <th>Coût (€)</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for d in linky_data[:10]:
        html += f"""
                        <tr>
                            <td>{d['date']}</td>
                            <td>{d['val']:.2f}</td>
                            <td>{d['cost']:.2f}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>

                <h3 style="margin-top: 20px; margin-bottom: 10px;">🔥 Gaz - Derniers 10 entrées</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Consommation (kWh)</th>
                            <th>Coût (€)</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for d in gas_data[:10]:
        html += f"""
                        <tr>
                            <td>{d['date']}</td>
                            <td>{d['val']:.2f}</td>
                            <td>{d['cost']:.2f}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>

                <h3 style="margin-top: 20px; margin-bottom: 10px;">🔋 Voiture (EV) - Derniers 10 relevés</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Recharge (kWh)</th>
                            <th>Coût (€)</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for d in car_data[:10]:
        html += f"""
                        <tr>
                            <td>{d['date']}</td>
                            <td>{d['val']:.2f}</td>
                            <td>{d['cost']:.2f}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>

            <div style="text-align: center; color: #999; font-size: 0.9em; margin-top: 30px;">
                <p>🗄️ Données provenant de ~/data/maison.db (SQLite)</p>
                <p>Linky API updates: Chaque jour à 2h | Reports: Chaque jour à 7h</p>
            </div>
        </div>
    </body>
    </html>
    """

    return render_template_string(html)

@app.route('/api/linky')
def api_linky():
    """API endpoint for Linky data"""
    data = load_linky_data()
    return jsonify(data)

@app.route('/api/gas')
def api_gas():
    """API endpoint for Gas data"""
    data = load_gas_data()
    return jsonify(data)

@app.route('/api/car')
def api_car():
    """API endpoint for Car data"""
    data = load_car_data()
    return jsonify(data)

@app.route('/health')
def health():
    """Health check endpoint"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'ok', 'database': 'sqlite'}), 200
    else:
        return jsonify({'status': 'error', 'database': 'sqlite'}), 500

if __name__ == '__main__':
    print("🚀 Starting Energy Dashboard (SQLite Version)")
    print(f"📁 Database: {DB_PATH}")
    print("🌐 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
