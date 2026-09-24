# Home Automation System

Comprehensive home energy monitoring and automated trading system for Raspberry Pi.

## 🏠 Features

- **Energy Monitoring**: Real-time tracking of electricity and gas consumption via Linky API
- **Automated Trading**: Bot DCA (Dollar Cost Averaging) for cryptocurrency on Kraken
- **Centralized Logging**: Loki + Promtail logging infrastructure
- **Advanced Monitoring**: 7 automated health checks with Telegram alerts
- **SQLite Database**: Persistent storage of energy, trading, and system metrics
- **Comprehensive Tests**: 88+ unit tests with ~92% code coverage
- **CI/CD Pipeline**: GitHub Actions workflows for automated testing and monitoring

## 📁 Project Structure

```
├── bot_kraken/              # DCA bot module
├── sonoff-energy/           # Energy monitoring module
├── .github/
│   └── workflows/           # GitHub Actions CI/CD
├── test_*.py                # Unit tests
├── *.py                     # Core scripts
├── *.js                     # Node.js utilities
└── data/
    └── maison.db            # SQLite database
```

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 4+ with Raspberry Pi OS
- Python 3.9+
- Node.js 14+ (for aggregator)
- SQLite3

### Installation

```bash
# Setup Phase 1 (Logging & Monitoring)
bash ~/setup_phase1_complete.sh

# Start services
bash ~/.loki/start-loki.sh &
bash ~/.loki/start-promtail.sh &
python3 ~/monitor_services_advanced.py &
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
bash run_all_tests.sh

# Or specific tests
pytest test_bot_dca.py -v
pytest test_app.py -v
pytest test_update_linky_history.py -v
```

## 📊 Monitoring

The monitoring system checks:
- Bot DCA process and error logs
- Linky API updates
- Email report delivery
- Disk space (alert >75%, critical >85%)
- Memory usage (alert >80%)
- CPU temperature (alert >70°C, critical >80°C)
- Kraken API connectivity

Alerts are sent via Telegram when thresholds are exceeded.

## 🗄️ Database

SQLite database at `~/data/maison.db` contains:
- **linky**: Electricity consumption records
- **gas**: Gas consumption records
- **car**: EV charging records
- **system_metrics**: CPU, memory, disk, temperature
- **trades**: DCA trading history

## 🧪 Test Coverage

- **bot_dca.py**: 16 tests - SMA calculations, Telegram alerts, execution
- **update_linky_history.py**: 21 tests - API parsing, date handling, cost calculations
- **app.py**: 33 tests - Portfolio calculations, data validation, edge cases
- **aggregator.js**: 34 tests - CSV operations, email, HTML generation

Target coverage: ~92% across all modules

## 🔄 CI/CD

GitHub Actions workflows:
- **test.yml**: Runs pytest on Python 3.9-3.11 with coverage reporting
- **monitoring.yml**: Health checks every 6 hours

## 📝 Environment Variables

Required:
- `LINKY_API_TOKEN`: MyElectricalData API token
- `LINKY_PDL`: Your PDL (electricity meter ID)
- `KRAKEN_API_KEY`: Kraken trading API key
- `KRAKEN_API_SECRET`: Kraken API secret
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID
- `GMAIL_USER`: Gmail account for reports
- `GMAIL_PASSWORD`: Gmail app password
- `EMAIL_RECIPIENT`: Primary recipient for reports
- `EMAIL_RECIPIENT_2`: Secondary recipient (optional)

## 📚 Documentation

- `PHASE1_COMPLETE_SUMMARY.md` - Logging & monitoring setup
- `PHASE1_DEPLOYMENT_GUIDE.md` - Detailed deployment instructions
- `PHASE3_SUMMARY.md` - Test suite documentation
- `TEST_QUICK_REFERENCE.md` - Testing commands

## 🤝 Contributing

Push changes to main/develop branches. CI/CD will automatically run tests and coverage checks.

## 📄 License

Private project - Home automation system
