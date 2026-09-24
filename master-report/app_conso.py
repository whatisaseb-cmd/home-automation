#!/usr/bin/env python3
"""
Energy Consumption Dashboard - SQLite Version with Charts & Manual Entry
Reads from ~/data/maison.db for Linky (electricity) and Gas data
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, jsonify

app = Flask(__name__)

# Paths
DB_PATH = os.path.expanduser('~/data/maison.db')
LOGS_DIR = os.path.expanduser('~/logs')

os.makedirs(LOGS_DIR, exist_ok=True)

def get_db_connection():
    """Connect to SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def load_linky_data(limit=365):
    """Load electricity data from SQLite"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT date, kwh, cost FROM linky ORDER BY date DESC LIMIT {limit}")
        rows = cursor.fetchall()
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in rows]
        conn.close()
        return sorted(data, key=lambda x: x['date'])
    except Exception as e:
        print(f"❌ Error loading Linky: {e}")
        conn.close()
        return []

def load_gas_data(limit=365):
    """Load gas data from SQLite"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT date, kwh, cost FROM gas ORDER BY date DESC LIMIT {limit}")
        rows = cursor.fetchall()
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in rows]
        conn.close()
        return sorted(data, key=lambda x: x['date'])
    except Exception as e:
        print(f"❌ Error loading Gas: {e}")
        conn.close()
        return []

def load_car_data(limit=365):
    """Load EV charging data from SQLite"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT date, kwh, cost FROM car ORDER BY date DESC LIMIT {limit}")
        rows = cursor.fetchall()
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in rows]
        conn.close()
        return sorted(data, key=lambda x: x['date'])
    except Exception as e:
        print(f"❌ Error loading Car: {e}")
        conn.close()
        return []

def insert_manual_entry(table, date_str, kwh, cost=None):
    """Insert or update manual entry in SQLite"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Calculate cost if not provided
        if cost is None:
            if table == 'gas':
                cost = kwh * 0.11548
            elif table == 'car':
                cost = kwh * 0.20
            else:
                cost = kwh * 0.19

        # Insert or replace
        cursor.execute(f"""
            INSERT OR REPLACE INTO {table} (date, kwh, cost)
            VALUES (?, ?, ?)
        """, (date_str, float(kwh), float(cost)))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error inserting entry: {e}")
        if conn:
            conn.close()
        return False

def get_year_comparison(table):
    """Get data grouped by month for year comparison"""
    conn = get_db_connection()
    if not conn:
        return {}

    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                strftime('%Y', date) as year,
                strftime('%m', date) as month,
                SUM(kwh) as total_kwh,
                SUM(cost) as total_cost
            FROM {table}
            GROUP BY year, month
            ORDER BY year DESC, month
        """)

        rows = cursor.fetchall()
        conn.close()

        # Organize by year
        years = {}
        for row in rows:
            year = row['year']
            month = row['month']
            if year not in years:
                years[year] = {}
            years[year][month] = {'kwh': row['total_kwh'], 'cost': row['total_cost']}

        return years
    except Exception as e:
        print(f"❌ Error getting comparison: {e}")
        conn.close()
        return {}

@app.route('/')
def index():
    """Main dashboard page"""
    linky_data = load_linky_data()
    gas_data = load_gas_data()
    car_data = load_car_data()

    # Calculate stats
    linky_total = sum(d['val'] for d in linky_data) if linky_data else 0
    linky_cost = sum(d['cost'] for d in linky_data) if linky_data else 0
    gas_total = sum(d['val'] for d in gas_data) if gas_data else 0
    gas_cost = sum(d['cost'] for d in gas_data) if gas_data else 0
    car_total = sum(d['val'] for d in car_data) if car_data else 0
    car_cost = sum(d['cost'] for d in car_data) if car_data else 0

    # Get year comparisons
    linky_years = get_year_comparison('linky')
    gas_years = get_year_comparison('gas')
    car_years = get_year_comparison('car')

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consommation Maison</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
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
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #333;
            }
            input {
                width: 100%;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #ddd;
                font-size: 1em;
            }
            button {
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
                background: #667eea;
                color: white;
                cursor: pointer;
                font-weight: 600;
            }
            button:hover {
                background: #5568d3;
            }
            .form-section {
                margin-bottom: 30px;
            }
            .badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 500;
                background: #e3f2fd;
                color: #1976d2;
            }
            .chart-container {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                position: relative;
                height: 400px;
            }
            .success {
                background: #4caf50;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                margin-bottom: 10px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Consommation Maison</h1>
                <p>Tableau de bord énergie - SQLite + Saisie manuelle</p>
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
                </div>
            </div>

            <!-- Saisie manuelle Gaz -->
            <div class="table-container form-section">
                <h2 style="margin-bottom: 20px;">➕ Ajouter une entrée Gaz</h2>
                <div id="gas-success" class="success">✅ Entrée gaz ajoutée avec succès!</div>
                <form id="gas-form" onsubmit="submitForm(event, 'gas')" style="display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 10px; align-items: end;">
                    <div>
                        <label>Date</label>
                        <input type="date" id="gas-date" required>
                    </div>
                    <div>
                        <label>Consommation (kWh)</label>
                        <input type="number" id="gas-kwh" step="0.01" required>
                    </div>
                    <div>
                        <label>Coût (€) - Optionnel</label>
                        <input type="number" id="gas-cost" step="0.01">
                    </div>
                    <button type="submit">Ajouter</button>
                </form>
            </div>

            <!-- Saisie manuelle Voiture -->
            <div class="table-container form-section">
                <h2 style="margin-bottom: 20px;">➕ Ajouter une entrée Voiture (EV)</h2>
                <div id="car-success" class="success">✅ Entrée voiture ajoutée avec succès!</div>
                <form id="car-form" onsubmit="submitForm(event, 'car')" style="display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 10px; align-items: end;">
                    <div>
                        <label>Date</label>
                        <input type="date" id="car-date" required>
                    </div>
                    <div>
                        <label>Recharge (kWh)</label>
                        <input type="number" id="car-kwh" step="0.01" required>
                    </div>
                    <div>
                        <label>Coût (€) - Optionnel</label>
                        <input type="number" id="car-cost" step="0.01">
                    </div>
                    <button type="submit">Ajouter</button>
                </form>
            </div>

            <!-- Graphiques comparaison années -->
            <div class="table-container">
                <h2 style="margin-bottom: 20px;">📈 Comparaison par mois (années antérieures)</h2>
                <div class="chart-container">
                    <canvas id="linkyChart"></canvas>
                </div>
            </div>

            <div class="table-container">
                <div class="chart-container">
                    <canvas id="gasChart"></canvas>
                </div>
            </div>

            <div class="table-container">
                <div class="chart-container">
                    <canvas id="carChart"></canvas>
                </div>
            </div>

            <!-- Tableau dernières données -->
            <div class="table-container">
                <h2 style="margin-bottom: 20px;">📋 Données Récentes</h2>

                <h3 style="margin-top: 20px; margin-bottom: 10px;">⚡ Électricité (Linky) - Derniers 15 jours</h3>
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

    for d in reversed(linky_data[-15:]):
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

            <div style="text-align: center; color: #999; font-size: 0.9em; margin-top: 30px; margin-bottom: 30px;">
                <p>🗄️ Données provenant de ~/data/maison.db (SQLite)</p>
                <p>Linky API updates: Chaque jour à 2h | Saisie manuelle en temps réel</p>
            </div>
        </div>

        <script>
            // Set today's date as default
            document.getElementById('gas-date').valueAsDate = new Date();
            document.getElementById('car-date').valueAsDate = new Date();

            async function submitForm(event, type) {
                event.preventDefault();
                const dateInput = document.getElementById(type + '-date').value;
                const kwhInput = document.getElementById(type + '-kwh').value;
                const costInput = document.getElementById(type + '-cost').value;

                const response = await fetch('/add_entry', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        table: type,
                        date: dateInput,
                        kwh: kwhInput,
                        cost: costInput || null
                    })
                });

                if (response.ok) {
                    document.getElementById(type + '-success').style.display = 'block';
                    document.getElementById(type + '-form').reset();
                    document.getElementById(type + '-date').valueAsDate = new Date();
                    setTimeout(() => {
                        document.getElementById(type + '-success').style.display = 'none';
                        location.reload();
                    }, 2000);
                } else {
                    alert('Erreur lors de l\'ajout de l\'entrée');
                }
            }

            // Charts
            const linkyYears = """ + json.dumps(linky_years) + """;
            const gasYears = """ + json.dumps(gas_years) + """;
            const carYears = """ + json.dumps(car_years) + """;

            function createChart(canvasId, data, label) {
                const ctx = document.getElementById(canvasId).getContext('2d');
                const months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];
                const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];

                const datasets = [];
                let colorIndex = 0;

                for (const [year, monthData] of Object.entries(data)) {
                    const values = [];
                    for (let m = 1; m <= 12; m++) {
                        const month = String(m).padStart(2, '0');
                        values.push(monthData[month]?.kwh || 0);
                    }

                    datasets.push({
                        label: year,
                        data: values,
                        borderColor: colors[colorIndex % colors.length],
                        backgroundColor: colors[colorIndex % colors.length] + '33',
                        borderWidth: 2,
                        tension: 0.3
                    });
                    colorIndex++;
                }

                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: months,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }

            createChart('linkyChart', linkyYears, '⚡ Électricité - Comparaison années');
            createChart('gasChart', gasYears, '🔥 Gaz - Comparaison années');
            createChart('carChart', carYears, '🔋 Voiture - Comparaison années');
        </script>
    </body>
    </html>
    """

    return render_template_string(html)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    """Add manual entry to database"""
    data = request.json

    success = insert_manual_entry(
        table=data['table'],
        date_str=data['date'],
        kwh=data['kwh'],
        cost=data['cost']
    )

    if success:
        return jsonify({'status': 'ok'}), 200
    else:
        return jsonify({'status': 'error'}), 500

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
    print("🚀 Starting Energy Dashboard v3 (SQLite + Charts + Manual Entry)")
    print(f"📁 Database: {DB_PATH}")
    print("🌐 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
