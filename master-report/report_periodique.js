#!/usr/bin/env node
/**
 * Weekly/Monthly Report Generator - SQLite Version
 * Generates HTML email reports with data from maison.db
 */

const sqlite3 = require('sqlite3').verbose();
const nodemailer = require('nodemailer');
const os = require('os');

/* --- CONFIGURATION --- */
const DB_PATH = os.homedir() + '/data/maison.db';
const EMAIL_RECIPIENT = '85seb.desprez@gmail.com';

// Tarifs Engie
const TARIFS = {
    linky_hc: 0.1740,   // Heures creuses
    gas: 0.11548
};
const ABONNEMENT_JOUR = 228.86 / 365;

// Détection Hebdo / Mensuel
const arg = process.argv[2] || 'hebdo';
const isMensuel = arg.toLowerCase() === 'mensuel' || arg.toLowerCase() === 'monthly';
const periodDays = isMensuel ? 30 : 7;
const reportTitle = isMensuel ? "Bilan Mensuel" : "Bilan Hebdomadaire";

const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: '85seb.desprez@gmail.com',
        pass: 'wpoxkpfnczceppzm'
    }
});

function getDbConnection() {
    return new Promise((resolve, reject) => {
        const db = new sqlite3.Database(DB_PATH, (err) => {
            if (err) reject(err);
            else resolve(db);
        });
    });
}

async function generateReport() {
    try {
        const db = await getDbConnection();

        let labels = [];
        let linkyData = [];
        let gasData = [];
        let carData = [];
        let linkySum = 0;
        let gasSum = 0;
        let carSum = 0;

        // Récupérer les données pour chaque jour
        for (let i = periodDays - 1; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const dStr = d.toISOString().split('T')[0];
            const displayDate = isMensuel ? d.getDate() : d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });

            // Récupérer Linky (électricité)
            const linkyVal = await new Promise((resolve) => {
                db.get("SELECT kwh FROM linky WHERE date = ?", [dStr], (err, row) => {
                    resolve(row ? parseFloat(row.kwh) : 0);
                });
            });

            // Récupérer Gaz
            const gasVal = await new Promise((resolve) => {
                db.get("SELECT kwh FROM gas WHERE date = ?", [dStr], (err, row) => {
                    resolve(row ? parseFloat(row.kwh) : 0);
                });
            });

            // Récupérer Voiture
            const carVal = await new Promise((resolve) => {
                db.get("SELECT kwh FROM car WHERE date = ?", [dStr], (err, row) => {
                    resolve(row ? parseFloat(row.kwh) : 0);
                });
            });

            labels.push(displayDate);
            linkyData.push(linkyVal);
            gasData.push(gasVal);
            carData.push(carVal);

            linkySum += linkyVal;
            gasSum += gasVal;
            carSum += carVal;
        }

        db.close();

        // Calculs des coûts
        const linkyCost = parseFloat((linkySum * TARIFS.linky_hc).toFixed(2));
        const gasCost = parseFloat((gasSum * TARIFS.gas).toFixed(2));
        const carCost = parseFloat((carSum * TARIFS.linky_hc).toFixed(2)); // Même tarif que HC
        const aboCost = parseFloat((ABONNEMENT_JOUR * periodDays).toFixed(2));
        const totalCost = parseFloat((linkyCost + gasCost + carCost + aboCost).toFixed(2));

        // Ratios pour affichage
        const linkyRatio = totalCost > 0 ? Math.round((linkyCost / totalCost) * 100) : 0;
        const gasRatio = totalCost > 0 ? Math.round((gasCost / totalCost) * 100) : 0;
        const carRatio = totalCost > 0 ? Math.round((carCost / totalCost) * 100) : 0;

        // Graphique via quickchart.io
        const chartConfig = {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Électricité (kWh)',
                        data: linkyData,
                        borderColor: '#007AFF',
                        backgroundColor: 'rgba(0, 122, 255, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: isMensuel ? 0 : 3
                    },
                    {
                        label: 'Gaz (kWh)',
                        data: gasData,
                        borderColor: '#FF9500',
                        backgroundColor: 'rgba(255, 149, 0, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: isMensuel ? 0 : 3
                    },
                    {
                        label: 'Voiture (kWh)',
                        data: carData,
                        borderColor: '#34C759',
                        backgroundColor: 'rgba(52, 199, 89, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: isMensuel ? 0 : 3
                    }
                ]
            },
            options: {
                legend: { position: 'bottom' },
                scales: { y: { beginAtZero: true } }
            }
        };
        const chartUrl = `https://quickchart.io/chart?c=${encodeURIComponent(JSON.stringify(chartConfig))}&w=600&h=350`;

        // Générer HTML
        const html = `
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f7; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { text-align: center; color: #1d1d1f; margin-bottom: 10px; font-size: 28px; }
                .subtitle { text-align: center; color: #86868b; font-size: 14px; margin-bottom: 30px; }
                .stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 30px; }
                .stat-card { background: #f9f9f9; padding: 15px; border-radius: 8px; text-align: center; }
                .stat-value { font-size: 24px; font-weight: 600; color: #1d1d1f; }
                .stat-label { font-size: 12px; color: #86868b; margin-top: 5px; text-transform: uppercase; }
                .chart { margin-bottom: 30px; text-align: center; }
                .chart img { max-width: 100%; height: auto; border-radius: 8px; }
                .breakdown { background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .breakdown-title { font-weight: 600; margin-bottom: 15px; color: #1d1d1f; }
                .breakdown-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e5e5e7; font-size: 14px; }
                .breakdown-row:last-child { border-bottom: none; }
                .breakdown-label { color: #555; }
                .breakdown-value { font-weight: 600; color: #1d1d1f; }
                .total-row { font-size: 16px; font-weight: 600; margin-top: 10px; padding-top: 10px; border-top: 2px solid #007AFF; }
                .footer { text-align: center; color: #86868b; font-size: 11px; margin-top: 30px; }
                .color-electric { color: #007AFF; }
                .color-gas { color: #FF9500; }
                .color-car { color: #34C759; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 ${reportTitle}</h1>
                <div class="subtitle">Rapport de consommation énergétique (${periodDays} jours)</div>

                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value color-electric">${linkySum.toFixed(1)}</div>
                        <div class="stat-label">⚡ Électricité (kWh)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value color-gas">${gasSum.toFixed(1)}</div>
                        <div class="stat-label">🔥 Gaz (kWh)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value color-car">${carSum.toFixed(1)}</div>
                        <div class="stat-label">🔋 Voiture (kWh)</div>
                    </div>
                </div>

                <div class="chart">
                    <img src="${chartUrl}" alt="Graphique consommation">
                </div>

                <div class="breakdown">
                    <div class="breakdown-title">💰 Détail des coûts</div>
                    <div class="breakdown-row">
                        <span class="breakdown-label color-electric">⚡ Électricité</span>
                        <span class="breakdown-value">${linkyCost.toFixed(2)}€ (${linkyRatio}%)</span>
                    </div>
                    <div class="breakdown-row">
                        <span class="breakdown-label color-gas">🔥 Gaz</span>
                        <span class="breakdown-value">${gasCost.toFixed(2)}€ (${gasRatio}%)</span>
                    </div>
                    <div class="breakdown-row">
                        <span class="breakdown-label color-car">🔋 Voiture</span>
                        <span class="breakdown-value">${carCost.toFixed(2)}€ (${carRatio}%)</span>
                    </div>
                    <div class="breakdown-row">
                        <span class="breakdown-label">📋 Abonnement</span>
                        <span class="breakdown-value">${aboCost.toFixed(2)}€</span>
                    </div>
                    <div class="breakdown-row total-row">
                        <span>TOTAL</span>
                        <span>${totalCost.toFixed(2)}€</span>
                    </div>
                </div>

                <div class="footer">
                    📊 Rapport généré à partir de la base de données SQLite<br>
                    Données: ${periodDays} derniers jours | Tarifs Engie réglementés
                </div>
            </div>
        </body>
        </html>
        `;

        // Envoyer email
        await transporter.sendMail({
            from: '85seb.desprez@gmail.com',
            to: EMAIL_RECIPIENT,
            subject: `${reportTitle} - Consommation énergétique (${new Date().toLocaleDateString('fr-FR')})`,
            html: html
        });

        console.log(`✅ ${reportTitle} envoyé avec succès!`);
    } catch (error) {
        console.error(`❌ Erreur: ${error.message}`);
        process.exit(1);
    }
}

// Lancer le rapport
generateReport();
