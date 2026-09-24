# 🚀 Phase 1: Logging Centralisé + Alertes (DEPLOYMENT GUIDE)

**Date**: 2026-09-24  
**Durée estimée**: 45 minutes  
**Niveau**: Moyen  
**Option sélectionnée**: A (Léger) - Loki + Promtail + Grafana

---

## 📋 What You'll Get

✅ **Loki** - Centralized log server (lightweight)  
✅ **Promtail** - Log shipper from all services  
✅ **Grafana** - Beautiful dashboards  
✅ **Advanced monitoring** - 7 critical checks with Telegram alerts  

---

## 🎯 Architecture

```
Services → Promtail → Loki (3100) ← Grafana (3000)
                ↓
            Alerts → Telegram
```

### What Gets Monitored:
1. **Bot DCA** - Process running + Error logs
2. **Linky Update** - Error detection
3. **Email Reports** - Success/failure
4. **Disk Usage** - >75% warning, >85% critical
5. **Memory** - >80% alert
6. **CPU Temperature** - >70° warning, >80° critical
7. **Kraken API** - Connectivity check

---

## 🚀 Deployment Steps

### Step 1: Copy Installation Scripts to Pi

```bash
# From your Mac
scp /tmp/install_loki_promtail.sh seb@192.168.3.49:/home/seb/
scp /tmp/install_grafana.sh seb@192.168.3.49:/home/seb/
scp /tmp/monitor_services_advanced.py seb@192.168.3.49:/home/seb/
scp /tmp/PHASE1_DEPLOYMENT_GUIDE.md seb@192.168.3.49:/home/seb/

# SSH to Pi
ssh seb@192.168.3.49
chmod +x ~/install_loki_promtail.sh ~/install_grafana.sh
```

### Step 2: Install Loki + Promtail

```bash
cd ~
bash install_loki_promtail.sh
```

**What it does:**
- Downloads Loki and Promtail (ARM64)
- Creates configuration files
- Sets up data directories
- Creates startup scripts

**Output should show:**
```
✅ Installation Complete!
✓ Directories created
✓ Loki downloaded
✓ Promtail downloaded
✓ Loki config created
✓ Promtail config created
✓ Startup scripts created
```

### Step 3: Start Loki (First Terminal)

```bash
# Terminal 1: Start Loki
cd ~
bash ~/.loki/start-loki.sh

# Should see:
# Starting Loki...
# level=info ts=2026-09-24T... msg="Loki started" version=v2.9.3
```

### Step 4: Start Promtail (Second Terminal)

```bash
# Terminal 2: Start Promtail
cd ~
bash ~/.loki/start-promtail.sh

# Should see:
# Starting Promtail...
# level=info ts=2026-09-24T... msg="Started Promtail" version=v2.9.3
```

### Step 5: Verify Loki is Working

```bash
# Terminal 3: Check Loki
curl http://localhost:3100/ready

# Should return "ready"
```

### Step 6: Query Logs from Loki

```bash
# Get Bot DCA logs
curl 'http://localhost:3100/loki/api/v1/query_range?query={job="bot_dca"}&limit=10'

# Should return JSON with log entries
```

### Step 7: Install Grafana (Optional but Recommended)

```bash
bash install_grafana.sh

# Wait for installation
# Access at: http://raspberry-pi.local:3000
# Login: admin / admin
```

### Step 8: Add Loki as Datasource in Grafana

1. Go to http://raspberry-pi.local:3000
2. Settings → Data Sources
3. Click "Add data source"
4. Select "Loki"
5. URL: `http://localhost:3100`
6. Save & Test

### Step 9: Setup Advanced Monitoring with Alerts

```bash
# Make monitoring script executable
chmod +x ~/monitor_services_advanced.py

# Test it manually
python3 ~/monitor_services_advanced.py

# Should output system status and any alerts
```

### Step 10: Add to Crontab for Regular Checks

```bash
crontab -e

# Add this line to run monitoring every 5 minutes
*/5 * * * * /usr/bin/python3 /home/seb/monitor_services_advanced.py >> /home/seb/logs/monitor.log 2>&1
```

---

## 📊 Testing the Setup

### Test 1: Verify Loki is receiving logs

```bash
# Wait 30 seconds for Promtail to collect logs
sleep 30

# Query Loki
curl 'http://localhost:3100/loki/api/v1/query_range?query={job="bot_dca"}&limit=5'
```

### Test 2: Verify Telegram Alerts

```bash
# Manually trigger an alert
python3 << 'EOF'
import os, urllib.request, urllib.parse

# Load env
env = {}
with open(os.path.expanduser('~/.env'), 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            env[key] = val

TOKEN = env.get('TELEGRAM_TOKEN')
CHAT_ID = env.get('TELEGRAM_CHAT_ID')

if TOKEN and CHAT_ID:
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = urllib.parse.urlencode({
        'chat_id': CHAT_ID,
        'text': '🧪 Test alert from Raspberry Pi monitoring'
    }).encode()
    try:
        urllib.request.urlopen(url, data, timeout=5)
        print("✅ Alert sent successfully!")
    except Exception as e:
        print(f"❌ Failed: {e}")
else:
    print("⚠️ Telegram not configured in .env")
EOF
```

### Test 3: Run Monitoring Check

```bash
python3 ~/monitor_services_advanced.py

# Should show:
# [timestamp] Starting comprehensive monitoring...
# ✅ Bot DCA running
# ✅ Linky OK
# ✅ Email OK
# ✅ All systems OK
```

---

## 🔌 Port Reference

| Service | Port | URL |
|---------|------|-----|
| Loki | 3100 | http://localhost:3100 |
| Promtail | 9080 | http://localhost:9080 |
| Grafana | 3000 | http://localhost:3000 |

---

## 📁 File Locations

```
/home/seb/.loki/
├── loki-linux-arm64          (Loki binary)
├── promtail-linux-arm64      (Promtail binary)
├── loki-config.yml           (Loki config)
├── promtail-config.yml       (Promtail config)
├── start-loki.sh             (Start script)
├── start-promtail.sh         (Start script)
├── data/                     (Log storage)
└── boltdb-shipper-*          (Index storage)

/home/seb/
├── monitor_services_advanced.py
├── ~/.loki/loki.service      (Systemd)
├── ~/.loki/promtail.service  (Systemd)
└── logs/monitor.log          (Monitoring output)
```

---

## 🔄 Enable Auto-Start (Systemd)

To make Loki/Promtail start automatically on reboot:

```bash
# Copy service files
sudo cp /home/seb/.loki/loki.service /etc/systemd/system/
sudo cp /home/seb/.loki/promtail.service /etc/systemd/system/

# Enable auto-start
sudo systemctl daemon-reload
sudo systemctl enable loki promtail

# Start services
sudo systemctl start loki promtail

# Check status
sudo systemctl status loki promtail
```

---

## 📊 Create Grafana Dashboards

### Dashboard 1: System Overview

**Query 1: Bot DCA Status**
```
{job="bot_dca"}
```

**Query 2: Error Count**
```
count_over_time({job="bot_dca"} | pattern `<_> ERROR <_>` [5m])
```

**Query 3: Disk Usage**
```
node_filesystem_avail_bytes{mountpoint="/"}
```

### Dashboard 2: Service Health

**Query: Last 24h of All Jobs**
```
{job=~"bot_dca|linky_update|email_reports"}
```

---

## 🚨 Alert Rules

The monitoring script checks:

| Check | Condition | Alert |
|-------|-----------|-------|
| Bot DCA | Not running | 🔴 CRITICAL |
| Bot DCA | Errors in log | ⚠️ WARNING |
| Linky | Errors in log | ⚠️ WARNING |
| Email | Errors in log | ⚠️ WARNING |
| Disk | > 85% | 🔴 CRITICAL |
| Disk | > 75% | 🟡 WARNING |
| Memory | > 80% | 🟡 WARNING |
| CPU Temp | > 80°C | 🔥 CRITICAL |
| CPU Temp | > 70°C | 🟡 WARNING |
| Kraken API | Down | ❌ CRITICAL |

---

## 🔧 Troubleshooting

### Loki won't start
```bash
# Check error
tail -f ~/.loki/loki.log

# Check port
lsof -i :3100

# Kill and restart
pkill loki
bash ~/.loki/start-loki.sh
```

### Promtail not collecting logs
```bash
# Check Promtail logs
tail -f ~/.loki/promtail.log

# Verify config
cat ~/.loki/promtail-config.yml

# Check log file paths exist
ls ~/bot_kraken/historique_dca.log
```

### Grafana can't connect to Loki
```bash
# Test connection manually
curl http://localhost:3100/ready

# Verify Loki is running
ps aux | grep loki
```

### No logs appearing in Loki
```bash
# Wait 30 seconds for Promtail to collect
sleep 30

# Query logs directly
curl 'http://localhost:3100/loki/api/v1/query?query={job="bot_dca"}'

# Check Promtail is running
ps aux | grep promtail
```

---

## 📈 Next Steps

1. ✅ **Phase 1 Complete** - Logging + Alerts setup
2. 🚀 **Phase 2** - Database migration (SQLite)
3. 🧪 **Phase 3** - Test coverage (88 tests, 92%)
4. ⚙️ **Phase 4** - CI/CD (GitHub Actions)

---

## 🎓 Monitoring Commands Quick Reference

```bash
# Start services manually
bash ~/.loki/start-loki.sh       # Terminal 1
bash ~/.loki/start-promtail.sh   # Terminal 2

# Query Loki API
curl 'http://localhost:3100/loki/api/v1/query_range?query={job="bot_dca"}&limit=10'

# Run monitoring check
python3 ~/monitor_services_advanced.py

# View Grafana
# Browser: http://raspberry-pi.local:3000

# Check service status
systemctl status loki
systemctl status promtail

# View logs
tail -f ~/.loki/loki.log
tail -f ~/.loki/promtail.log

# Kill and restart
pkill loki promtail
bash ~/.loki/start-loki.sh &
bash ~/.loki/start-promtail.sh &
```

---

## ✅ Success Checklist

- [ ] Loki started successfully
- [ ] Promtail started successfully
- [ ] curl http://localhost:3100/ready returns "ready"
- [ ] Logs appear in Loki API queries
- [ ] Grafana accessible at http://localhost:3000
- [ ] Grafana can query Loki
- [ ] Monitor script runs without errors
- [ ] Telegram alerts work
- [ ] Monitoring added to crontab
- [ ] Services set to auto-start (systemd)

---

**Phase 1 Complete!** You now have centralized logging and comprehensive monitoring with Telegram alerts. 🎉

