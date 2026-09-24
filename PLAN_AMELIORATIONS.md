# 🚀 Plan d'Améliorations - Système Maison Seb

**Date**: 2026-09-24  
**État Actuel**: ✅ Production Ready (Baseline établie)  
**Objectif**: Évolutivité, Fiabilité, Monitoring, Automatisation

---

## 📊 État Actuel du Système

### Infrastructure
```
✅ Raspberry Pi 4 (système principal)
✅ Services actifs via cron + PM2
✅ 22+ scripts (Python, Node.js, Shell)
✅ 3 environnements virtuels (bot_kraken, pea_env, etc)
✅ 7+ fichiers CSV avec données historiques
✅ Logs dispersés dans différents dossiers
✅ Double email + Telegram configuré
```

### Points Forts Actuels
- ✅ Code corrigé et sécurisé
- ✅ Tests unitaires (16 tests)
- ✅ Credentials en .env
- ✅ Crontab bien configuré
- ✅ Rapports quotidiens fonctionnels

### Points Faibles à Adresser
- ⚠️ Pas de base de données (CSV partout)
- ⚠️ Logs dispersés, pas centralisés
- ⚠️ Pas de monitoring/alertes
- ⚠️ Pas de tests pour 80% du code
- ⚠️ Pas d'interface de visualisation
- ⚠️ Pas de CI/CD
- ⚠️ Pas de documentation auto

---

## 🎯 Améliorations Priorisées

### PRIORITÉ 1️⃣: FIABILITÉ & MONITORING (2-3 jours)

#### 1.1 Logging Centralisé
**Problème**: Les logs sont partout (fichiers différents, pas de structure)  
**Solution**: ELK Stack ou Loki + Prometheus

```
Bénéfices:
- Retrouver les erreurs facilement
- Dashboard centralisé
- Alertes automatiques si problème
- Historique accessible

Effort: Moyen (4-6h)
Impact: Très Haut
```

**Implémentation suggérée**:
```bash
# Option A (léger): Loki + Promtail
- Installer Loki sur Pi
- Configurer Promtail pour chaque script
- Grafana pour visualiser

# Option B (complet): ELK Stack
- Elasticsearch + Logstash + Kibana
- Plus puissant mais plus gourmand en ressources
```

#### 1.2 Alertes Critiques
**Problème**: Si un bot crash, tu ne le sais que le lendemain  
**Solution**: Monitorer les processus + alertes Telegram

```
Cas à monitorer:
- Bot DCA crash → alerte immédiate
- Email fail → alerte
- API Kraken down → alerte
- Espace disque faible → alerte
- RAM utilisée > 80% → alerte

Outil suggéré: Prometheus + Alertmanager
```

---

### PRIORITÉ 2️⃣: BASE DE DONNÉES (3-4 jours)

#### 2.1 Migrer CSV → SQLite (Quick Win)
**Problème**: CSV c'est pas scalable (lent, pas de requêtes complexes)  
**Solution**: SQLite (facile, no-setup, parfait pour Pi)

```
Bénéfices:
- Requêtes SQL (JOIN, GROUP BY, etc)
- Backups automatiques
- Transactions (atomicité)
- Meilleure performance

Migration:
- Linky CSV → table linky
- Gas CSV → table gas
- Trades CSV → table trades
- Car CSV → table car

Effort: 2-3h
Impact: Moyen-Haut (future-proof)
```

#### 2.2 Backup Automatique DB
```
Ajouter au crontab:
0 2 * * * sqlite3 ~/data/maison.db ".dump" | gzip > ~/backups/maison_$(date +%Y%m%d).sql.gz
```

---

### PRIORITÉ 3️⃣: TESTS & QUALITÉ CODE (3-4 jours)

#### 3.1 Augmenter Couverture Tests à 85%+
**Actuel**: 78% (bot_dca seulement)  
**Cible**: 85%+ pour tous les modules

```
À tester:
□ update_linky_history.py (5-6 tests)
□ app.py (Streamlit) (3-4 tests)
□ bot_rapport.py (4-5 tests)
□ aggregator.js (3-4 tests)

Total: ~20 tests supplémentaires
```

#### 3.2 Integration Tests
```
Tester le flow complet:
- Récupérer données API
- Traiter données
- Envoyer rapports
- Vérifier réception

Outils: pytest + pytest-vcr (mock API calls)
```

---

### PRIORITÉ 4️⃣: CI/CD PIPELINE (2 jours)

#### 4.1 GitHub Actions
```yaml
name: Tests & Lint
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov=. --cov-fail-under=80
      - run: black --check .
      - run: pylint bot_kraken/
```

**Bénéfices**:
- Auto-tester avant merge
- Empêcher regressions
- Versioning propre

---

### PRIORITÉ 5️⃣: DASHBOARD & VISUALISATION (3-4 jours)

#### 5.1 Grafana Dashboard
```
Afficher en temps réel:
- Graphiques Linky (consommation électricité)
- Portefeuille BTC (prix, performance)
- État système (CPU, RAM, Disk)
- Sentiment marché crypto
- Historique rapports
```

#### 5.2 Web UI Simple
```
Alternative légère: Flask + Chart.js
- Page simple pour voir les stats
- Pas besoin de Grafana (lourd pour Pi)
- Accessible depuis navigateur

Effort: 4-5h
```

---

### PRIORITÉ 6️⃣: OPTIMISATIONS BUSINESS (2-3 jours)

#### 6.1 Bot DCA Amélioré
```
Idées:
- RSI indicator (force du trend)
- Fibonacci retracements
- Volume profile
- MACD signal
- Ajustement dynamique des montants

Plus "intelligent" pour décider d'acheter
```

#### 6.2 Rapport Portefeuille Enrichi
```
Ajouter:
- Allocation par secteur (crypto, actions, immobilier)
- Projection 5/10 ans avec différents scénarios
- Comparaison vs indices (BTC, S&P 500, etc)
- Risk assessment (drawdown max, volatilité)
```

#### 6.3 Prédictions & ML
```
Modèles simples:
- Consommation électricité prévue (ARIMA)
- Prix BTC (Prophet - Facebook)
- Alerte anomalies (Isolation Forest)

Effort: 2-3 jours (libraires prêtes)
Impact: Modéré
```

---

## 📋 Architecture Recommandée

### Avant (Actuelle)
```
Scripts → Email/Telegram
   ↓
  CSV Files
```

### Après (Proposée)
```
Scripts → SQLite DB ← Backups
   ↓
Logs → Loki → Grafana (Monitoring)
   ↓
Alertes → Telegram
   ↓
API → Flask → Web UI
   ↓
Tests (CI/CD GitHub Actions)
```

---

## 📈 Roadmap Suggérée

### Semaine 1
- [ ] Logging centralisé (Loki)
- [ ] Alertes critiques (Prometheus)
- [ ] Augmenter tests à 85%

### Semaine 2
- [ ] Migrer CSV → SQLite
- [ ] Backup automatique DB
- [ ] GitHub Actions CI/CD

### Semaine 3
- [ ] Grafana Dashboard
- [ ] Web UI Flask simple
- [ ] Tests intégration complets

### Semaine 4
- [ ] Bot DCA amélioré (RSI, MACD)
- [ ] Rapport enrichi
- [ ] ML pour prédictions

---

## 💰 Estimation Effort Total

| Tâche | Effort | Impact |
|-------|--------|--------|
| Logging Centralisé | 4-6h | ⭐⭐⭐⭐⭐ |
| Alertes | 3-4h | ⭐⭐⭐⭐ |
| SQLite + Backup | 2-3h | ⭐⭐⭐⭐ |
| Tests +7% | 8-10h | ⭐⭐⭐⭐ |
| CI/CD | 3-4h | ⭐⭐⭐ |
| Grafana | 4-5h | ⭐⭐⭐⭐ |
| Bot Amélioré | 6-8h | ⭐⭐⭐⭐⭐ |
| ML Prédictions | 6-8h | ⭐⭐⭐ |
| **TOTAL** | **36-50h** | |

---

## 🎓 Lessons Learned

### Ce Qui Marche Bien ✅
1. Code review + tests early = confiance
2. .env pour secrets = sécurité
3. Logging structuré = debugging facile
4. Crontab simple = fiable

### Ce À Améliorer ⚠️
1. Pas de monitoring = blind spots
2. CSV = pas scalable
3. Logs partout = hard to find issues
4. Pas de CI/CD = risque de regression

---

## 🚀 Quick Wins (1-2 jours)

Si tu veux commencer léger:

1. **Loki + Promtail** (4h)
   - Centraliser les logs
   - Dashboard Loki

2. **Alertes Telegram** (2h)
   - Si bot crash → alerte immédiate
   - Si API fail → alerte

3. **SQLite for Linky** (2h)
   - Juste migrer la table linky
   - Garder autres en CSV pour commencer

Total: **8h** pour avoir monitoring + DB commencé

---

## Questions à Répondre Ensemble

1. **Priorités**: Monitoring d'abord ou DB d'abord?
2. **Infrastructure**: Ajouter plus de RAM/storage au Pi?
3. **Complexité**: Jusqu'où aller avec ML?
4. **Scale**: Veux-tu ajouter d'autres capteurs/services?

---

**Prêt à discuter! Quelles sont tes priorités?** 🎯
