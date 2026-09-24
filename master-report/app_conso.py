#!/usr/bin/env python3
"""
Energy Consumption Dashboard - SQLite Version with Simple Forms & Charts
Réglementé Engie tariffs auto-calculated
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Paths
DB_PATH = os.path.expanduser('~/data/maison.db')
LOGS_DIR = os.path.expanduser('~/logs')

os.makedirs(LOGS_DIR, exist_ok=True)

# Tarifs réglementés Engie (€/kWh)
TARIFS = {
    'linky_hc': 0.16039,  # Heures creuses
    'linky_hp': 0.19209,  # Heures pleines
    'gas': 0.11548,        # Gaz
    'car': 0.20            # EV charging average
}

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

def insert_manual_entry(table, date_str, kwh):
    """Insert or update manual entry in SQLite with auto-calculated cost"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Auto-calculate cost based on tarif
        if table == 'gas':
            cost = float(kwh) * TARIFS['gas']
        elif table == 'car':
            cost = float(kwh) * TARIFS['car']
        else:  # linky
            cost = float(kwh) * TARIFS['linky_hc']

        # Insert or replace
        cursor.execute(f"""
            INSERT OR REPLACE INTO {table} (date, kwh, cost)
            VALUES (?, ?, ?)
        """, (date_str, float(kwh), round(cost, 4)))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error inserting entry: {e}")
        if conn:
            conn.close()
        return False

def get_monthly_data(table):
    """Get data grouped by month (all years)"""
    conn = get_db_connection()
    if not conn:
        return {}

    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                strftime('%Y', date) as year,
                strftime('%m', date) as month,
                SUM(kwh) as total_kwh
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
            years[year][month] = float(row['total_kwh']) if row['total_kwh'] else 0

        return years
    except Exception as e:
        print(f"❌ Error getting monthly data: {e}")
        if conn:
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

    # Get monthly data for charts
    linky_months = get_monthly_data('linky')
    gas_months = get_monthly_data('gas')
    car_months = get_monthly_data('car')

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
            .form-inline {
                display: grid;
                grid-template-columns: 2fr 1fr auto;
                gap: 15px;
                align-items: end;
            }
            input {
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
                padding: 12px 15px;
                border-radius: 6px;
                margin-bottom: 15px;
                display: none;
            }
            .tarif-info {
                font-size: 0.9em;
                color: #666;
                margin-top: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Consommation Maison</h1>
                <p>Tableau de bord énergie - Tarifs Engie réglementés</p>
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

            <!-- Saisie Gaz -->
            <div class="table-container">
                <h2 style="margin-bottom: 15px;">🔥 Ajouter Gaz</h2>
                <div id="gas-success" class="success">✅ Entrée ajoutée!</div>
                <form id="gas-form" onsubmit="submitForm(event, 'gas')" class="form-inline">
                    <div>
                        <input type="date" id="gas-date" required>
                    </div>
                    <div>
                        <input type="number" id="gas-kwh" placeholder="kWh" step="0.01" required>
                    </div>
                    <button type="submit">Ajouter</button>
                </form>
                <div class="tarif-info">💰 Tarif: """ + f"{TARIFS['gas']:.5f}" + """ €/kWh (Engie réglementé)</div>
            </div>

            <!-- Saisie Voiture -->
            <div class="table-container">
                <h2 style="margin-bottom: 15px;">🔋 Ajouter Recharge EV</h2>
                <div id="car-success" class="success">✅ Entrée ajoutée!</div>
                <form id="car-form" onsubmit="submitForm(event, 'car')" class="form-inline">
                    <div>
                        <input type="date" id="car-date" required>
                    </div>
                    <div>
                        <input type="number" id="car-kwh" placeholder="kWh" step="0.01" required>
                    </div>
                    <button type="submit">Ajouter</button>
                </form>
                <div class="tarif-info">💰 Tarif: """ + f"{TARIFS['car']:.5f}" + """ €/kWh (Moyenne)</div>
            </div>

            <!-- Graphiques -->
            <div class="table-container">
                <h2 style="margin-bottom: 20px;">📈 Comparaison par mois</h2>
                <div class="chart-container">
                    <canvas id="linkyChart"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="gasChart"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="carChart"></canvas>
                </div>
            </div>

            <!-- Données récentes -->
            <div class="table-container">
                <h2 style="margin-bottom: 20px;">📋 Données Récentes</h2>

                <h3 style="margin-top: 0; margin-bottom: 10px;">⚡ Électricité - Derniers 15 jours</h3>
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
                <p>🗄️ Données SQLite | Tarifs Engie réglementés appliqués automatiquement</p>
            </div>
        </div>

        <script>
            // Set today's date
            document.getElementById('gas-date').valueAsDate = new Date();
            document.getElementById('car-date').valueAsDate = new Date();

            async function submitForm(event, type) {
                event.preventDefault();
                const date = document.getElementById(type + '-date').value;
                const kwh = document.getElementById(type + '-kwh').value;

                const response = await fetch('/add_entry', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({table: type, date: date, kwh: kwh})
                });

                if (response.ok) {
                    document.getElementById(type + '-success').style.display = 'block';
                    document.getElementById(type + '-form').reset();
                    document.getElementById(type + '-date').valueAsDate = new Date();
                    setTimeout(() => location.reload(), 1500);
                } else {
                    alert('Erreur');
                }
            }

            function createChart(canvasId, data, title) {
                const ctx = document.getElementById(canvasId).getContext('2d');
                const months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];
                const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];

                const datasets = [];
                let colorIndex = 0;

                // Sort years descending
                const sortedYears = Object.keys(data).sort().reverse();

                for (const year of sortedYears) {
                    const monthData = data[year];
                    const values = [];
                    for (let m = 1; m <= 12; m++) {
                        const month = String(m).padStart(2, '0');
                        values.push(monthData[month] || 0);
                    }

                    datasets.push({
                        label: year,
                        data: values,
                        borderColor: colors[colorIndex % colors.length],
                        backgroundColor: colors[colorIndex % colors.length] + '33',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    });
                    colorIndex++;
                }

                new Chart(ctx, {
                    type: 'line',
                    data: {labels: months, datasets: datasets},
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {mode: 'index', intersect: false},
                        plugins: {
                            legend: {position: 'top'},
                            title: {display: true, text: title}
                        },
                        scales: {y: {beginAtZero: true}}
                    }
                });
            }

            const linkyMonths = """ + json.dumps(linky_months) + """;
            const gasMonths = """ + json.dumps(gas_months) + """;
            const carMonths = """ + json.dumps(car_months) + """;

            createChart('linkyChart', linkyMonths, '⚡ Électricité - Comparaison mensuelle');
            createChart('gasChart', gasMonths, '🔥 Gaz - Comparaison mensuelle');
            createChart('carChart', carMonths, '🔋 Voiture - Comparaison mensuelle');
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
        kwh=data['kwh']
    )

    return jsonify({'status': 'ok' if success else 'error'}), (200 if success else 500)

@app.route('/health')
def health():
    """Health check endpoint"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'ok'}), 200
    return jsonify({'status': 'error'}), 500

if __name__ == '__main__':
    print("🚀 Energy Dashboard v4 (Simple Forms + Year Comparison)")
    print(f"📁 Database: {DB_PATH}")
    print("🌐 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
