#!/bin/bash

# Phase 1: Complete Setup - Loki + Promtail + Grafana + Advanced Monitoring
# One-click installation and configuration

set -e

echo "🚀 Phase 1 - Complete Setup (Loki + Promtail + Grafana + Monitoring)"
echo "====================================================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
LOKI_DIR="/home/seb/.loki"
LOG_DIR="/home/seb/logs"

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
command -v curl >/dev/null 2>&1 || { echo -e "${RED}curl is required${NC}"; exit 1; }
command -v wget >/dev/null 2>&1 || { echo -e "${RED}wget is required${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}python3 is required${NC}"; exit 1; }
echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Step 2: Create directories
echo -e "${YELLOW}Step 2: Creating directories...${NC}"
mkdir -p "$LOKI_DIR"
mkdir -p "$LOKI_DIR/data"
mkdir -p "$LOKI_DIR/boltdb-shipper-active"
mkdir -p "$LOKI_DIR/boltdb-shipper-cache"
mkdir -p "$LOG_DIR"
mkdir -p "$HOME/.grafana"
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 3: Install Loki and Promtail
echo -e "${YELLOW}Step 3: Installing Loki and Promtail...${NC}"
cd "$LOKI_DIR"

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    ARCH="arm64"
elif [ "$ARCH" = "armv7l" ]; then
    ARCH="armv7"
fi

echo "Architecture: $ARCH"

# Download Loki
if [ ! -f "loki-linux-$ARCH" ]; then
    echo "Downloading Loki..."
    LOKI_VERSION="2.9.3"
    wget -q "https://github.com/grafana/loki/releases/download/v${LOKI_VERSION}/loki-linux-${ARCH}.zip"
    unzip -q "loki-linux-${ARCH}.zip" || true
    chmod +x "loki-linux-${ARCH}" 2>/dev/null || true
    rm -f "loki-linux-${ARCH}.zip"
    echo "✓ Loki ready"
else
    echo "✓ Loki already present"
fi

# Download Promtail
if [ ! -f "promtail-linux-$ARCH" ]; then
    echo "Downloading Promtail..."
    PROMTAIL_VERSION="2.9.3"
    wget -q "https://github.com/grafana/loki/releases/download/v${PROMTAIL_VERSION}/promtail-linux-${ARCH}.zip"
    unzip -q "promtail-linux-${ARCH}.zip" || true
    chmod +x "promtail-linux-${ARCH}" 2>/dev/null || true
    rm -f "promtail-linux-${ARCH}.zip"
    echo "✓ Promtail ready"
else
    echo "✓ Promtail already present"
fi

echo -e "${GREEN}✓ Loki and Promtail installed${NC}"
echo ""

# Step 4: Create configuration files (using here docs from previous script)
echo -e "${YELLOW}Step 4: Creating configuration files...${NC}"

cat > "$LOKI_DIR/loki-config.yml" << 'EOF'
auth_enabled: false

ingester:
  chunk_idle_period: 3m
  max_chunk_age: 1h
  max_streams_match_order: 0
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 100
  ingestion_burst_size_mb: 200

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

server:
  http_listen_port: 3100
  log_level: info

storage_config:
  boltdb_shipper:
    active_index_directory: /home/seb/.loki/boltdb-shipper-active
    cache_location: /home/seb/.loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /home/seb/.loki/data

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
EOF

cat > "$LOKI_DIR/promtail-config.yml" << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /home/seb/.loki/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: bot_dca
    static_configs:
      - targets:
          - localhost
        labels:
          job: bot_dca
          __path__: /home/seb/bot_kraken/historique_dca.log

  - job_name: linky_update
    static_configs:
      - targets:
          - localhost
        labels:
          job: linky_update
          __path__: /home/seb/sonoff-energy/cron_linky.log

  - job_name: email_reports
    static_configs:
      - targets:
          - localhost
        labels:
          job: email_reports
          __path__: /home/seb/master-report/cron_log.txt
EOF

echo -e "${GREEN}✓ Configuration files created${NC}"
echo ""

# Step 5: Create startup scripts
echo -e "${YELLOW}Step 5: Creating startup scripts...${NC}"

cat > "$LOKI_DIR/start-loki.sh" << 'EOF'
#!/bin/bash
cd /home/seb/.loki
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; elif [ "$ARCH" = "armv7l" ]; then ARCH="armv7"; fi
exec ./loki-linux-${ARCH} -config.file=loki-config.yml
EOF
chmod +x "$LOKI_DIR/start-loki.sh"

cat > "$LOKI_DIR/start-promtail.sh" << 'EOF'
#!/bin/bash
cd /home/seb/.loki
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; elif [ "$ARCH" = "armv7l" ]; then ARCH="armv7"; fi
exec ./promtail-linux-${ARCH} -config.file=promtail-config.yml
EOF
chmod +x "$LOKI_DIR/start-promtail.sh"

echo -e "${GREEN}✓ Startup scripts created${NC}"
echo ""

# Step 6: Copy monitoring script
echo -e "${YELLOW}Step 6: Setting up monitoring...${NC}"
chmod +x /home/seb/monitor_services_advanced.py
echo -e "${GREEN}✓ Monitoring script ready${NC}"
echo ""

# Step 7: Create cron job
echo -e "${YELLOW}Step 7: Adding monitoring to crontab...${NC}"
# Check if already in crontab
if ! crontab -l 2>/dev/null | grep -q "monitor_services_advanced"; then
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/python3 /home/seb/monitor_services_advanced.py >> /home/seb/logs/monitor.log 2>&1") | crontab -
    echo -e "${GREEN}✓ Monitoring added to crontab (every 5 minutes)${NC}"
else
    echo -e "${GREEN}✓ Monitoring already in crontab${NC}"
fi
echo ""

# Step 8: Summary
echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}✅ Phase 1 Setup Complete!${NC}"
echo -e "${GREEN}===================================================${NC}"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1️⃣  Start Loki (Terminal 1):"
echo "   bash ~/.loki/start-loki.sh"
echo ""
echo "2️⃣  Start Promtail (Terminal 2):"
echo "   bash ~/.loki/start-promtail.sh"
echo ""
echo "3️⃣  Verify Loki is working:"
echo "   curl http://localhost:3100/ready"
echo ""
echo "4️⃣  View monitoring status:"
echo "   python3 ~/monitor_services_advanced.py"
echo ""
echo "5️⃣  Optional - Install Grafana:"
echo "   sudo apt-get update && sudo apt-get install -y grafana-server"
echo "   sudo systemctl start grafana-server"
echo "   # Then: http://localhost:3000 (admin/admin)"
echo ""
echo "📊 Important Ports:"
echo "   Loki:      http://localhost:3100"
echo "   Promtail:  http://localhost:9080"
echo "   Grafana:   http://localhost:3000"
echo ""
echo "📁 Important Directories:"
echo "   Loki config:     ~/.loki/"
echo "   Monitoring logs: ~/logs/"
echo "   Log storage:     ~/.loki/data/"
echo ""
echo "✨ You're all set! Monitoring will run automatically every 5 minutes."
echo "   Check for alerts in Telegram!"
echo ""
