const TOKEN = 'UVB340_dmQfQ540md9SXR02B_08py7m-aEaSCb8_Mrs=';
const PDL = '06307525305736'; // Électricité (Linky)
const PCE = '06307670023502'; // Gaz (Gazpar)

async function test() {
    // On teste pour "Avant-hier" (J-2) pour être sûr que la donnée a eu le temps d'arriver
    const d = new Date();
    d.setDate(d.getDate() - 2); 
    const dateStr = d.toISOString().split('T')[0];

    const urls = {
        elec: `https://myelectricaldata.fr/daily_consumption/${PDL}/start/${dateStr}/end/${dateStr}`,
        gaz: `https://myelectricaldata.fr/gaz/daily_consumption/${PCE}/start/${dateStr}/end/${dateStr}`
    };

    console.log(`\n🔍 Lancement du diagnostic pour la date du : ${dateStr}\n`);

    for (const [name, url] of Object.entries(urls)) {
        console.log(`--- Test ${name.toUpperCase()} ---`);
        try {
            const res = await fetch(url, { headers: { 'Authorization': TOKEN } });
            const data = await res.json();
            console.log(JSON.stringify(data, null, 2), '\n');
        } catch (e) {
            console.log(`❌ Erreur ${name}:`, e.message, '\n');
        }
    }
}
test();
