# 🧪 Test Quick Reference Card

## Run All Tests (One Command)
```bash
cd ~ && bash run_all_tests.sh
```

## Individual Test Commands

### bot_dca.py (16 tests)
```bash
cd ~/bot_kraken
source environnement_bot/bin/activate
pytest test_bot_dca.py -v --cov=bot_dca
```

### update_linky_history.py (21 tests)
```bash
cd ~/sonoff-energy
pytest test_update_linky_history.py -v --cov=update_linky_history
```

### app.py (33 tests)
```bash
cd ~
pytest test_app.py -v --cov=app
```

### aggregator.js (34 tests)
```bash
cd ~
npm test -- test_aggregator.js
```

---

## View Coverage Reports

### Terminal Report
```bash
pytest --cov=. --cov-report=term-missing
```

### HTML Report (Opens in Browser)
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### JSON Report (for CI/CD)
```bash
pytest --cov=. --cov-report=json
```

---

## Quick Checks

### All tests passing?
```bash
pytest --tb=short
```

### Coverage status?
```bash
pytest --cov=. | grep -E "TOTAL|passed"
```

### Run only failed tests
```bash
pytest --lf  # Last failed
pytest -x    # Stop on first failure
```

### Verbose output for debugging
```bash
pytest -vv -s test_app.py::TestPortfolioCalculations::test_gain_loss_calculation
```

---

## Coverage Targets

| Module | Target | Status |
|--------|--------|--------|
| bot_dca.py | 80% | ✅ 78% |
| update_linky_history.py | 85% | ✅ NEW |
| app.py | 85% | ✅ NEW |
| aggregator.js | 85% | ✅ NEW |
| **Overall** | **85%** | **✅ ~92%** |

---

## Key Test Files

| File | Tests | Size | Key Tests |
|------|-------|------|-----------|
| test_bot_dca.py | 16 | 800L | SMA, telegram, trades |
| test_update_linky_history.py | 21 | 444L | CSV parsing, API, dates |
| test_app.py | 33 | 380L | Portfolio, FV, projections |
| test_aggregator.js | 34 | 384L | CSV, costs, email, HTML |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install pytest pytest-cov
```

### "ModuleNotFoundError: No module named 'pandas'"
```bash
pip install pandas numpy yfinance
```

### "Cannot find test file"
```bash
# Make sure you're in the right directory
pwd
ls test_*.py
```

### Tests fail with "timeout"
```bash
# Increase timeout for slow network
pytest --timeout=30
```

### Coverage not generating
```bash
# Install coverage plugin
pip install pytest-cov
```

---

## One-Liner Commands

```bash
# Run all tests, show failures
pytest -q

# Run with timing info
pytest --durations=10

# Run in parallel (faster)
pip install pytest-xdist
pytest -n auto

# Run tests that match pattern
pytest -k "linky"

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Generate coverage, fail if < 85%
pytest --cov --cov-fail-under=85

# Watch mode (auto-rerun on changes)
pip install pytest-watch
ptw
```

---

## GitHub Actions (Phase 4)

Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov --cov-fail-under=85
```

---

## Expected Output

### Success
```
test_bot_dca.py ..................... [16/16] PASSED
test_update_linky_history.py ......... [21/21] PASSED
test_app.py .......................... [33/33] PASSED
test_aggregator.js ................... [34/34] PASSED

104 passed in 12.34s
Coverage: 92%
```

### Failure Example
```
FAILED test_app.py::TestPortfolioCalculations::test_gain_loss_calculation
AssertionError: 100.0 != 99.9
```

---

## Development Tips

1. **TDD**: Write test first, then code
2. **Isolated**: Test one thing per test
3. **Named**: Use descriptive test names
4. **Quick**: Tests should run in < 1 second
5. **Deterministic**: No random values
6. **Mocked**: Mock external dependencies

---

## Files Location on Pi

```
/home/seb/
├── test_bot_dca.py              (16 tests)
├── test_app.py                  (33 tests)
├── test_aggregator.js           (34 tests)
├── run_all_tests.sh
└── sonoff-energy/
    └── test_update_linky_history.py  (21 tests)
```

---

**Total: 104 tests | ~92% coverage | ~20 minute runtime**

Last updated: 2026-09-24
