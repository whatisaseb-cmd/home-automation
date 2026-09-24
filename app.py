import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Mon Dashboard PEA 2050", layout="wide")
st.title("📈 Mon Suivi de Portefeuille PEA")

# Données du portefeuille
data = {
    'Ticker': ['CW8.PA', 'EUSA.PA', 'VUSA.PA'],
    'Nom': ['MSCI World', 'S&P 500', 'S&P 500 Acc'],
    'Quantité': [10, 5, 2],
    'Prix_Moyen_Achat': [410.0, 380.0, 85.0]
}
df_portfolio = pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_current_prices(tickers):
    """Récupère les prix avec gestion d'erreur robuste."""
    prices = {}
    for t in tickers:
        try:
            ticker = yf.Ticker(t)
            hist = ticker.history(period="1d")
            if hist.empty:
                logger.warning(f"Aucune donnée pour {t}")
                prices[t] = None
            else:
                price = hist['Close'].iloc[-1]
                prices[t] = float(price) if pd.notna(price) else None
        except Exception as e:
            logger.error(f"Erreur récupération {t}: {e}")
            prices[t] = None
    return prices

with st.spinner('Mise à jour des cours de bourse...'):
    current_prices = get_current_prices(df_portfolio['Ticker'].tolist())

# Ajouter les prix et calculer les valeurs
df_portfolio['Prix_Actuel'] = df_portfolio['Ticker'].map(current_prices)
df_portfolio['Valeur_Actuelle'] = df_portfolio['Quantité'] * df_portfolio['Prix_Actuel']
df_portfolio['Investissement_Initial'] = df_portfolio['Quantité'] * df_portfolio['Prix_Moyen_Achat']
df_portfolio['Plus_Moins_Value'] = df_portfolio['Valeur_Actuelle'] - df_portfolio['Investissement_Initial']

# Calculer la performance en gérant les NaN
def calc_perf(row):
    if pd.isna(row['Investissement_Initial']) or row['Investissement_Initial'] == 0:
        return 0.0
    if pd.isna(row['Plus_Moins_Value']):
        return 0.0
    return (row['Plus_Moins_Value'] / row['Investissement_Initial']) * 100

df_portfolio['Performance_%'] = df_portfolio.apply(calc_perf, axis=1)

# Filtrer les lignes avec prix valides
df_valid = df_portfolio.dropna(subset=['Prix_Actuel'])

if len(df_valid) == 0:
    st.error("❌ Impossible de récupérer les prix actuels. Vérifiez votre connexion Internet.")
    st.stop()

total_valeur = df_valid['Valeur_Actuelle'].sum()
total_investi = df_valid['Investissement_Initial'].sum()
performance_globale = ((total_valeur - total_investi) / total_investi * 100) if total_investi > 0 else 0.0

# Affichage
col1, col2, col3 = st.columns(3)
col1.metric("Valeur Totale", f"{total_valeur:,.2f} €")
col2.metric("Gain/Perte", f"{total_valeur - total_investi:,.2f} €", f"{performance_globale:.2f}%")
col3.metric("Investissement Initial", f"{total_investi:,.2f} €")

st.divider()

st.subheader("Détails des lignes")
st.dataframe(
    df_valid[['Nom', 'Quantité', 'Prix_Moyen_Achat', 'Prix_Actuel', 'Valeur_Actuelle', 'Performance_%']],
    use_container_width=True,
    hide_index=True
)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Répartition du Portefeuille")
    fig_pie = px.pie(df_valid, values='Valeur_Actuelle', names='Nom', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("Projection vers 2050")
    mensuel = st.number_input("Versement mensuel prévu (€)", value=200, min_value=0)
    rendement = st.slider("Rendement annuel espéré (%)", 1.0, 12.0, 7.0)

    annees = 2050 - datetime.now().year
    mois_totaux = annees * 12
    taux_mensuel = (1 + rendement/100)**(1/12) - 1

    if taux_mensuel > 0:
        future_val = (total_valeur * (1 + taux_mensuel)**mois_totaux +
                     mensuel * (((1 + taux_mensuel)**mois_totaux - 1) / taux_mensuel))
    else:
        future_val = total_valeur + mensuel * mois_totaux

    if pd.notna(future_val) and future_val > 0:
        st.info(f"En continuant ainsi, votre capital estimé en 2050 serait de : **{future_val:,.2f} €**")
    else:
        st.warning("Erreur dans le calcul de projection")
