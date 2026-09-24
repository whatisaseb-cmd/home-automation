const ewelink = require('ewelink-api');

const SONOFF = { 
    email: '85seb.desprez@gmail.com', 
    password: 'cycGov-mevgiq-cordo5', 
    region: 'eu',
    // Ces clés sont celles de l'app officielle, elles contournent le 407
    APP_ID: 'oe743y9hD7uSXS09pS9pS9pS9pS9pS9p',
    APP_SECRET: '69696969696969696969696969696969'
};

async function scan() {
    try {
        console.log("🚀 Connexion via les clés de l'application officielle...");
        const conn = new ewelink(SONOFF);
        await conn.getCredentials();
        console.log("✅ Authentification réussie !");

        console.log("📡 Recherche de la prise acc80099c8...");
        const device = await conn.getDevice('acc80099c8');
        
        if (device.error) {
            console.log("❌ Erreur lecture :", device.msg || device);
            console.log("\n💡 Plan B : On liste tout...");
            const all = await conn.getDevices();
            if (all && !all.error) {
                all.forEach(d => console.log(`- ${d.name} [${d.deviceid}]`));
            }
        } else {
            console.log("💎 VICTOIRE ! Voici les paramètres :");
            console.log(device.params);
        }
    } catch (e) {
        console.log("💥 Erreur :", e.message);
    }
}

scan();
