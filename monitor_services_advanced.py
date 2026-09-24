#!/usr/bin/env python3
"""
Advanced monitoring with comprehensive alerts
- Monitor bot status
- Check API connectivity
- Track system resources
- Send Telegram alerts
"""

import os
import subprocess
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import time

# Load env vars
def load_env():
    env = {}
    with open(os.path.expanduser('~/.env'), 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                env[key] = val
    return env

ENV = load_env()
TELEGRAM_TOKEN = ENV.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = ENV.get('TELEGRAM_CHAT_ID', '')

# State file to avoid duplicate alerts
STATE_FILE = os.path.expanduser('~/.monitor_state.json')

def load_state():
    """Load previous state to avoid duplicate alerts"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    """Save state for next check"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def send_alert(message, severity='⚠️'):
    """Send Telegram alert"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f'{severity} {message} (No Telegram configured)')
        return

    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = urllib.parse.urlencode({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': f'{severity} {message}',
        'parse_mode': 'Markdown'
    }).encode()

    try:
        with urllib.request.urlopen(url, data, timeout=5) as response:
            print(f'✅ Alert sent: {message[:50]}...')
    except Exception as e:
        print(f'❌ Alert failed: {e}')

def check_process_running(name, cmd_pattern):
    """Check if process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', cmd_pattern],
                              capture_output=True, timeout=3)
        return result.returncode == 0
    except:
        return False

def check_log_errors(filepath, hours=1):
    """Check for errors in log file"""
    if not os.path.exists(filepath):
        return False

    try:
        mtime = os.path.getmtime(filepath)
        now = datetime.now().timestamp()
        age_hours = (now - mtime) / 3600

        if age_hours > hours:
            return False

        with open(filepath, 'r') as f:
            content = f.read()
            return 'ERROR' in content or 'error' in content or 'ERREUR' in content
    except:
        return False

def check_api_connectivity(api_url, timeout=5):
    """Check if API endpoint is reachable"""
    try:
        response = urllib.request.urlopen(api_url, timeout=timeout)
        return response.status == 200
    except:
        return False

def get_disk_usage():
    """Get disk usage percentage"""
    try:
        result = subprocess.run(['df', '-h', os.path.expanduser('~')],
                              capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        for line in lines:
            if '%' in line:
                usage = int(line.split()[-2].rstrip('%'))
                return usage
    except:
        return 0

def get_memory_usage():
    """Get memory usage percentage"""
    try:
        result = subprocess.run(['free', '-h'],
                              capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Mem:' in line:
                parts = line.split()
                total = float(parts[1].replace('G', '').replace('M', ''))
                used = float(parts[2].replace('G', '').replace('M', ''))
                usage = (used / total) * 100
                return int(usage)
    except:
        return 0

def get_cpu_temp():
    """Get CPU temperature (Raspberry Pi)"""
    try:
        result = subprocess.run(['vcgencmd', 'measure_temp'],
                              capture_output=True, text=True, timeout=5)
        temp_str = result.stdout.replace('temp=', '').replace("'C", '').strip()
        return float(temp_str)
    except:
        return 0

def check_kraken_api():
    """Check Kraken API connectivity"""
    try:
        result = subprocess.run(['curl', '-s', 'https://api.kraken.com/0/public/SystemStatus'],
                              capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout)
        return data.get('result', {}).get('status') == 'online'
    except:
        return False

def monitor():
    """Main monitoring function"""
    state = load_state()
    alerts = []

    print(f'\n[{datetime.now()}] Starting comprehensive monitoring...\n')

    # ✅ 1. Bot DCA Status
    print('🤖 Checking Bot DCA...')
    if not check_process_running('bot_dca', 'bot_dca.py'):
        alerts.append('🚨 *Bot DCA is NOT running*')
        send_alert('🤖 Bot DCA crash detected!', '🔴')
    else:
        print('   ✅ Bot DCA running')
        # Check for errors
        if check_log_errors(os.path.expanduser('~/bot_kraken/historique_dca.log'), hours=1):
            alerts.append('⚠️ *Bot DCA errors in last hour*')
            send_alert('Bot DCA reported errors', '⚠️')

    # ✅ 2. Linky Update Status
    print('⚡ Checking Linky update...')
    if check_log_errors(os.path.expanduser('~/sonoff-energy/cron_linky.log'), hours=2):
        alerts.append('⚠️ *Linky update failed*')
        send_alert('Linky update failed', '⚠️')
    else:
        print('   ✅ Linky OK')

    # ✅ 3. Email Reports Status
    print('📧 Checking email reports...')
    if check_log_errors(os.path.expanduser('~/master-report/cron_log.txt'), hours=2):
        alerts.append('⚠️ *Email report failed*')
        send_alert('Email report failed', '⚠️')
    else:
        print('   ✅ Email OK')

    # ✅ 4. Disk Usage
    print('💾 Checking disk space...')
    disk_usage = get_disk_usage()
    print(f'   Disk: {disk_usage}%')
    if disk_usage > 85:
        alerts.append(f'🔴 *CRITICAL: Disk {disk_usage}%*')
        send_alert(f'Disk critical: {disk_usage}%', '🔴')
    elif disk_usage > 75:
        prev_disk = state.get('disk_warning')
        if prev_disk != disk_usage:
            send_alert(f'Disk warning: {disk_usage}%', '⚠️')
            state['disk_warning'] = disk_usage

    # ✅ 5. Memory Usage
    print('🧠 Checking memory...')
    mem_usage = get_memory_usage()
    print(f'   Memory: {mem_usage}%')
    if mem_usage > 80:
        alerts.append(f'🟡 *Memory high: {mem_usage}%*')
        send_alert(f'Memory high: {mem_usage}%', '🟡')

    # ✅ 6. CPU Temperature
    print('🌡️ Checking CPU temperature...')
    cpu_temp = get_cpu_temp()
    print(f'   Temp: {cpu_temp}°C')
    if cpu_temp > 80:
        alerts.append(f'🔥 *CPU overheating: {cpu_temp}°C*')
        send_alert(f'CPU hot: {cpu_temp}°C', '🔥')
    elif cpu_temp > 70:
        print('   ⚠️ Temperature elevated')

    # ✅ 7. Kraken API Status
    print('🔗 Checking Kraken API...')
    if not check_kraken_api():
        prev_kraken = state.get('kraken_down')
        if not prev_kraken:
            send_alert('Kraken API unreachable', '❌')
            state['kraken_down'] = True
    else:
        print('   ✅ Kraken API OK')
        state['kraken_down'] = False

    # Save state for next run
    save_state(state)

    # ✅ Summary
    print('\n' + '='*50)
    if alerts:
        print(f'⚠️  ALERTS DETECTED: {len(alerts)}')
        for alert in alerts:
            print(f'   {alert}')
    else:
        print('✅ All systems OK')
    print('='*50 + '\n')

    return len(alerts) == 0

if __name__ == '__main__':
    success = monitor()
    exit(0 if success else 1)
