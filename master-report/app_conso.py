#!/usr/bin/env python3
"""
Energy Consumption Dashboard - Apple Design + Mobile Responsive
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

DB_PATH = os.path.expanduser('~/data/maison.db')
TARIFS = {
    'linky': 0.1740,  # Engie 9kVA heures creuses
    'gas': 0.11548,   # Engie gaz
    'car': 0.1740     # EV charging at home (HC rate)
}

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def load_linky_data(limit=365):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT date, kwh, cost FROM linky ORDER BY date DESC LIMIT {limit}")
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in cursor.fetchall()]
        conn.close()
        return sorted(data, key=lambda x: x['date'])
    except:
        conn.close()
        return []

def load_gas_data(limit=365):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT date, kwh, cost FROM gas ORDER BY date DESC LIMIT {limit}")
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in cursor.fetchall()]
        conn.close()
        return sorted(data, key=lambda x: x['date'])
    except:
        conn.close()
        return []

def load_car_data(limit=365):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT date, kwh, cost FROM car ORDER BY date DESC LIMIT {limit}")
        data = [{'date': row['date'], 'val': row['kwh'], 'cost': row['cost']} for row in cursor.fetchall()]
        conn.close()
        return sorted(data, key=lambda x: x['date'])
    except:
        conn.close()
        return []

def insert_manual_entry(table, date_str, kwh):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cost = float(kwh) * TARIFS.get(table, 0.20)
        cursor.execute(f"INSERT OR REPLACE INTO {table} (date, kwh, cost) VALUES (?, ?, ?)",
                      (date_str, float(kwh), round(cost, 4)))
        conn.commit()
        conn.close()
        return True
    except:
        if conn:
            conn.close()
        return False

def get_monthly_data(table):
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT strftime('%Y', date) as year, strftime('%m', date) as month, SUM(kwh) as total_kwh
            FROM {table}
            GROUP BY year, month
            ORDER BY year DESC, month
        """)
        years = {}
        for row in cursor.fetchall():
            year, month = row['year'], row['month']
            if year not in years:
                years[year] = {}
            years[year][month] = float(row['total_kwh']) if row['total_kwh'] else 0
        conn.close()
        return years
    except:
        conn.close()
        return {}

@app.route('/')
def index():
    linky_data = load_linky_data()
    gas_data = load_gas_data()
    car_data = load_car_data()

    linky_total = sum(d['val'] for d in linky_data) if linky_data else 0
    linky_cost = sum(d['cost'] for d in linky_data) if linky_data else 0
    gas_total = sum(d['val'] for d in gas_data) if gas_data else 0
    gas_cost = sum(d['cost'] for d in gas_data) if gas_data else 0
    car_total = sum(d['val'] for d in car_data) if car_data else 0
    car_cost = sum(d['cost'] for d in car_data) if car_data else 0

    linky_months = get_monthly_data('linky')
    gas_months = get_monthly_data('gas')
    car_months = get_monthly_data('car')

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
        <title>Consommation</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                -webkit-tap-highlight-color: transparent;
            }

            html, body {
                height: 100%;
                width: 100%;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
                background: #f5f5f7;
                color: #1d1d1f;
                font-size: 16px;
                line-height: 1.6;
                -webkit-font-smoothing: antialiased;
                -webkit-text-size-adjust: 100%;
            }

            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 0 16px;
            }

            .header {
                padding: 32px 0 20px;
                text-align: center;
            }

            .header h1 {
                font-size: 32px;
                font-weight: 700;
                letter-spacing: -0.5px;
                margin-bottom: 8px;
            }

            .header p {
                font-size: 15px;
                color: #86868b;
                font-weight: 400;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 12px;
                margin-bottom: 24px;
            }

            .stat-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
            }

            .stat-card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.12);
                transform: translateY(-2px);
            }

            .stat-card-title {
                font-size: 14px;
                color: #86868b;
                font-weight: 500;
                margin-bottom: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .stat-card-value {
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 8px;
                color: #1d1d1f;
            }

            .stat-card-cost {
                font-size: 14px;
                color: #555;
            }

            .stat-card-count {
                font-size: 12px;
                color: #a1a1a6;
                margin-top: 8px;
            }

            .color-electric { border-top: 3px solid #007AFF; }
            .color-gas { border-top: 3px solid #FF9500; }
            .color-car { border-top: 3px solid #34C759; }

            .section {
                margin-bottom: 24px;
            }

            .section-title {
                font-size: 17px;
                font-weight: 600;
                margin-bottom: 12px;
                color: #1d1d1f;
                margin-top: 20px;
            }

            .form-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                margin-bottom: 16px;
            }

            .form-inline {
                display: grid;
                grid-template-columns: 1fr 1fr auto;
                gap: 12px;
                align-items: flex-end;
            }

            @media (max-width: 600px) {
                .form-inline {
                    grid-template-columns: 1fr;
                }
            }

            input {
                padding: 12px;
                border: 1px solid #e5e5e7;
                border-radius: 8px;
                font-size: 16px;
                font-family: inherit;
                transition: border-color 0.2s;
            }

            input:focus {
                outline: none;
                border-color: #007AFF;
                box-shadow: 0 0 0 3px rgba(0,122,255,0.1);
            }

            button {
                padding: 12px 24px;
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }

            button:active {
                background: #0051D5;
                transform: scale(0.96);
            }

            button:hover {
                background: #0051D5;
            }

            .tarif-info {
                font-size: 12px;
                color: #86868b;
                margin-top: 8px;
            }

            .success {
                background: #34C759;
                color: white;
                padding: 12px 16px;
                border-radius: 8px;
                margin-bottom: 12px;
                display: none;
                font-size: 14px;
                font-weight: 500;
            }

            .chart-container {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                margin-bottom: 16px;
                position: relative;
                height: 300px;
            }

            @media (max-width: 600px) {
                .chart-container {
                    height: 250px;
                }
            }

            .chart-title {
                font-size: 15px;
                font-weight: 600;
                margin-bottom: 16px;
                color: #1d1d1f;
            }

            .data-table {
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                overflow: hidden;
            }

            table {
                width: 100%;
                border-collapse: collapse;
            }

            th {
                background: #f5f5f7;
                padding: 12px 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 600;
                color: #555;
                text-transform: uppercase;
                letter-spacing: 0.3px;
                border-bottom: 1px solid #e5e5e7;
            }

            td {
                padding: 12px 16px;
                border-bottom: 1px solid #f0f0f0;
                font-size: 14px;
            }

            tr:last-child td {
                border-bottom: none;
            }

            tr:hover {
                background: #fafafa;
            }

            .footer {
                text-align: center;
                color: #86868b;
                font-size: 12px;
                padding: 40px 0;
                margin-top: 20px;
            }

            @media (max-width: 600px) {
                .container {
                    padding: 0 12px;
                }

                .header {
                    padding: 24px 0 16px;
                }

                .header h1 {
                    font-size: 28px;
                }

                .stats-grid {
                    grid-template-columns: 1fr;
                    gap: 12px;
                }

                .form-inline {
                    grid-template-columns: 1fr;
                }

                .section-title {
                    font-size: 16px;
                }

                table {
                    font-size: 13px;
                }

                th, td {
                    padding: 10px 12px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Consommation</h1>
                <p>Tableau de bord énergie maison</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card color-electric">
                    <div class="stat-card-title">⚡ Électricité</div>
                    <div class="stat-card-value">""" + f"{linky_total:.0f}" + """</div>
                    <div class="stat-card-cost">kWh • """ + f"{linky_cost:.2f}" + """€</div>
                    <div class="stat-card-count">""" + str(len(linky_data)) + """ jours</div>
                </div>

                <div class="stat-card color-gas">
                    <div class="stat-card-title">🔥 Gaz</div>
                    <div class="stat-card-value">""" + f"{gas_total:.0f}" + """</div>
                    <div class="stat-card-cost">kWh • """ + f"{gas_cost:.2f}" + """€</div>
                    <div class="stat-card-count">""" + str(len(gas_data)) + """ relevés</div>
                </div>

                <div class="stat-card color-car">
                    <div class="stat-card-title">🔋 Voiture</div>
                    <div class="stat-card-value">""" + f"{car_total:.0f}" + """</div>
                    <div class="stat-card-cost">kWh • """ + f"{car_cost:.2f}" + """€</div>
                    <div class="stat-card-count">""" + str(len(car_data)) + """ recharges</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Ajouter des données</div>

                <div class="form-card">
                    <div style="font-weight: 600; margin-bottom: 12px;">🔥 Gaz</div>
                    <div id="gas-success" class="success">✅ Entrée ajoutée</div>
                    <form id="gas-form" onsubmit="submitForm(event, 'gas')" class="form-inline">
                        <input type="date" id="gas-date" required>
                        <input type="number" id="gas-kwh" placeholder="kWh" step="0.01" required>
                        <button type="submit">Ajouter</button>
                    </form>
                    <div class="tarif-info">Tarif: 0.11548 €/kWh (Engie)</div>
                </div>

                <div class="form-card">
                    <div style="font-weight: 600; margin-bottom: 12px;">🔋 Recharge EV</div>
                    <div id="car-success" class="success">✅ Entrée ajoutée</div>
                    <form id="car-form" onsubmit="submitForm(event, 'car')" class="form-inline">
                        <input type="date" id="car-date" required>
                        <input type="number" id="car-kwh" placeholder="kWh" step="0.01" required>
                        <button type="submit">Ajouter</button>
                    </form>
                    <div class="tarif-info">Tarif: 0.1740 €/kWh (HC)</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Comparaison par mois</div>

                <div class="chart-container">
                    <div class="chart-title">⚡ Électricité</div>
                    <canvas id="linkyChart"></canvas>
                </div>

                <div class="chart-container">
                    <div class="chart-title">🔥 Gaz</div>
                    <canvas id="gasChart"></canvas>
                </div>

                <div class="chart-container">
                    <div class="chart-title">🔋 Voiture</div>
                    <canvas id="carChart"></canvas>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Données récentes</div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Consommation</th>
                                <th>Coût</th>
                            </tr>
                        </thead>
                        <tbody>
    """

    for d in reversed(linky_data[-10:]):
        html += f"<tr><td>{d['date']}</td><td>{d['val']:.1f} kWh</td><td>{d['cost']:.2f}€</td></tr>"

    html += """
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="footer">
                Données en temps réel • Mis à jour """ + datetime.now().strftime("%H:%M") + """
            </div>
        </div>

        <script>
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
                }
            }

            function createChart(canvasId, data, title) {
                const ctx = document.getElementById(canvasId).getContext('2d');
                const months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];
                const colors = ['#007AFF', '#FF9500', '#34C759', '#FF3B30', '#5856D6'];

                const datasets = [];
                let colorIndex = 0;
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
                        backgroundColor: colors[colorIndex % colors.length] + '20',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 3,
                        pointBackgroundColor: colors[colorIndex % colors.length]
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
                            legend: {position: 'top', labels: {padding: 15, font: {size: 12}}},
                            filler: {propagate: true}
                        },
                        scales: {y: {beginAtZero: true, grid: {drawBorder: false, color: '#f0f0f0'}}}
                    }
                });
            }

            const linkyMonths = """ + json.dumps(linky_months) + """;
            const gasMonths = """ + json.dumps(gas_months) + """;
            const carMonths = """ + json.dumps(car_months) + """;

            createChart('linkyChart', linkyMonths, 'Électricité');
            createChart('gasChart', gasMonths, 'Gaz');
            createChart('carChart', carMonths, 'Voiture');
        </script>
    </body>
    </html>
    """

    return render_template_string(html)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    data = request.json
    success = insert_manual_entry(data['table'], data['date'], data['kwh'])
    return jsonify({'status': 'ok' if success else 'error'}), (200 if success else 500)

@app.route('/health')
def health():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'ok'}), 200
    return jsonify({'status': 'error'}), 500

if __name__ == '__main__':
    print("🚀 Energy Dashboard v5 (Apple Design + Mobile Responsive)")
    app.run(host='0.0.0.0', port=5000, debug=False)
