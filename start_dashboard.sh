#!/bin/bash
# Start Energy Dashboard Server
# Add to crontab with: @reboot /home/seb/start_dashboard.sh

cd /home/seb/master-report

# Kill any existing process on port 5000
kill $(lsof -t -i :5000) 2>/dev/null || true
sleep 1

# Start the dashboard
nohup python3 app_conso.py > /home/seb/logs/dashboard.log 2>&1 &

echo "🚀 Dashboard started on http://localhost:5000"
