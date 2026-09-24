const ewelink = require('ewelink-api');

/* --- CONFIGURATION --- */
const email = '85seb.desprez@gmail.com';
const password = 'cycGov-mevgiq-cordo5';
const region = 'eu'; 
const deviceId = 'acc80099c8'; 
const logFile = '/home/seb/sonoff-energy/last_reading.txt';

const connection = new ewelink({ email, password, region });

async function run() {
    const action = process.argv[2]; 
    const status = await connection.getDevicePowerUsage(deviceId);
    
let currentTotal = parseFloat(status.monthly); 
    if (isNaN(currentTotal)) currentTotal = 0;

    if (action === 'start') {
        if (currentTotal > 0) {
            require('fs').writeFileSync(logFile, currentTotal.toString());
            console.log(`✅ Index de départ enregistré : ${currentTotal} kWh`);
        } else {
            console.log("⚠️ Lecture à 0 ou échec API Sonoff. Fichier non modifié.");
        }
    } else if (action === 'end') {
        let startTotal = parseFloat(require('fs').readFileSync(logFile, 'utf8'));
        if (isNaN(startTotal)) startTotal = 0;
        
        const consumption = (currentTotal - startTotal).toFixed(3);
        
        // Couleur dynamique basée sur la consommation (ajustez les seuils si besoin)
        let color = "#2ecc71"; // Vert par défaut
        if (consumption > 2.0) color = "#f39c12"; // Orange au-dessus de 2kWh
        if (consumption > 3.0) color = "#e74c3c"; // Rouge au-dessus de 3kWh

        // Génération de l'e-mail HTML
        const html = `
        <html>
        <head>
        <style>
          :root { --bg: #f4f4f4; --card: #ffffff; --text: #333333; --border: #eeeeee; }
          @media (prefers-color-scheme: dark) {
            :root { --bg: #1c1c1e; --card: #2c2c2e; --text: #f2f2f7; --border: #38383a; }
          }
          body { font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text); padding: 20px; }
          .card { max-width: 350px; margin: auto; background: var(--card); padding: 25px; border-radius: 12px; border-top: 8px solid ${color}; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
          h2 { margin-top: 0; font-size: 18px;}
          .big-number { font-size: 38px; font-weight: bold; color: ${color}; text-align: center; margin: 20px 0; }
          table { width: 100%; border-collapse: collapse; font-size: 14px; }
          td { padding: 8px 0; border-bottom: 1px solid var(--border); }
          .right { text-align: right; font-weight: bold; }
        </style>
        </head>
        <body>
          <div class="card">
            <h2>⚡ Bilan Nocturne</h2>
            <p style="font-size: 12px; color: gray;">Mesure de 23h30 à 07h30</p>
            <div class="big-number">${consumption} <span style="font-size: 20px;">kWh</span></div>
            <table>
              <tr><td>Index Départ</td><td class="right">${startTotal.toFixed(3)}</td></tr>
              <tr><td>Index Arrivée</td><td class="right">${currentTotal.toFixed(3)}</td></tr>
            </table>
          </div>
        </body>
        </html>
        `;
        console.log(html);
    }
}

run();
