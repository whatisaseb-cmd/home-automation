# 🚀 Checklist Session 2 - Tokens Reset

**Timing**: Tokens reset dans 1h30 → On attaque après!

---

## ⚡ Action Immédiate (Dès que tu reviens)

### 1️⃣ VÉRIFIER LES NOUVEAUX TOKENS
```bash
# Aller chercher les nouveaux tokens/clés
# (à faire rapidement après reset)

# Questions:
- Kraken API key change?
- Telegram token change?
- Linky API token change?
```

### 2️⃣ METTRE À JOUR .env
```bash
ssh seb@192.168.3.49 "nano ~/.env"
# Remplacer les anciens tokens par les nouveaux
```

### 3️⃣ TESTER LES CONNEXIONS
```bash
# Vérifier que tout reconnecte bien
- Bot DCA
- Bot Rapport
- Update Linky
- Aggregator (email)
```

---

## 📋 PLAN DE SESSION 2

### Phase 1: QUICK WINS (1-2h) ⭐⭐⭐⭐⭐

**Logging Centralisé + Alertes**

```bash
# 1. Installer Loki (léger pour Pi)
sudo docker pull grafana/loki:latest
docker run -d -p 3100:3100 grafana/loki:latest

# 2. Configurer Promtail pour les logs
# 3. Dashboard Loki pour voir les logs
# 4. Alertes Telegram si problème
```

**Impact**: Tu peux monitorer tous les scripts en temps réel! 👀

---

### Phase 2: DATABASE MIGRATION (1h) ⭐⭐⭐⭐

**SQLite pour Linky**

```bash
# 1. Créer DB: maison.db
sqlite3 ~/data/maison.db

# 2. Créer table linky depuis CSV
CREATE TABLE linky (
  date TEXT PRIMARY KEY,
  kwh REAL,
  cost REAL
);

# 3. Charger données historiques
# 4. Update script pour écrire dans DB au lieu de CSV
```

**Impact**: Plus de CSV! Requêtes SQL, backups faciles! 🗄️

---

### Phase 3: TESTS (1-2h) ⭐⭐⭐⭐

**Augmenter couverture à 85%+**

```bash
# Créer test_update_linky.py (5-6 tests)
# Créer test_bot_rapport.py (4-5 tests)
# Lancer: pytest --cov=. (voir couverture)
```

**Impact**: Confiance qu'on ne casse rien! ✅

---

### Phase 4: CI/CD (30min-1h) ⭐⭐⭐

**GitHub Actions**

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest --cov=. --cov-fail-under=80
```

**Impact**: Jamais pusher du code cassé! 🛡️

---

## 🎯 FOCUS SESSION 2

**Objectif**: Infrastructure solide (Logging + DB + Tests)

**Non-objectif**: Features nuevas, ML, Dashboard (Phase 3)

---

## 📝 Checklist de Préparation (Dès Maintenant)

- [ ] Mémoriser où retrouver les nouveaux tokens
- [ ] Lister tous les services qui utilisent tokens/API keys
- [ ] Préparer commandes test pour chaque service
- [ ] Vérifier espaces disque disponible pour Loki
- [ ] Télécharger Loki/Promtail docs

---

## 🔗 Services à Checker Post-Reset

```
✓ Kraken API (bot_dca, bot_rapport)
✓ Telegram (tous les bots)
✓ Linky API (update_linky)
✓ Gmail (aggregator.js email)
✓ Ring API (aggregator.js - optional)
```

---

## 💬 Questions à Répondre Quand tu Reviens

1. **Tokens**: Kraken key réinitie? Linky API nouveau?
2. **Priorité**: On commande par Logging ou DB?
3. **Contraintes**: Espace disque limité? CPU faible?
4. **Scope**: On vise juste Phase 1 ou on fait 2+3?

---

**À bientôt! On va faire un SUPER travail! 🚀**
