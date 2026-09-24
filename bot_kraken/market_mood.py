import requests
import json
from datetime import datetime

def get_crypto_sentiment():
    url = "https://api.alternative.me/fng/"
    try:
        response = requests.get(url, timeout=10).json()
        data = response['data'][0]
        score = int(data['value'])
        label = data['value_classification']
        
        # Mise en forme pour votre rapport
        mood_report = f"\n--- MÉTÉO DU MARCHÉ CRYPTO ---\n"
        mood_report += f"Score Sentiment : {score}/100 ({label})\n"
        
        # Décision forte basée sur le score
        if score < 25:
            mood_report += "Conseil : Opportunité d'achat (Peur extrême).\n"
        elif score > 75:
            mood_report += "Conseil : Prudence (Euphorie excessive).\n"
        else:
            mood_report += "Conseil : Tendance neutre.\n"
            
        return mood_report
    except:
        return "\n--- MÉTÉO DU MARCHÉ : Indisponible ---\n"

if __name__ == "__main__":
    print(get_crypto_sentiment())
