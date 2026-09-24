#!/bin/bash

# Phase 3 - Comprehensive Test Suite Runner
# This script runs all tests and generates a coverage report

set -e

echo "🧪 Phase 3 - Test Suite Runner"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create results directory
RESULTS_DIR="./test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "📁 Results will be saved to: $RESULTS_DIR"
echo ""

# Test 1: bot_dca.py
echo -e "${YELLOW}1/4 Testing bot_dca.py...${NC}"
if [ -f "$HOME/bot_kraken/test_bot_dca.py" ]; then
    cd "$HOME/bot_kraken"
    if source environnement_bot/bin/activate 2>/dev/null; then
        pytest test_bot_dca.py -v --cov=bot_dca --cov-report=json:"$RESULTS_DIR/bot_dca_coverage.json" 2>&1 | tee "$RESULTS_DIR/bot_dca_tests.log" || true
        deactivate
        echo -e "${GREEN}✓ bot_dca.py tests completed${NC}"
    else
        echo -e "${RED}✗ Could not activate bot_kraken environment${NC}"
    fi
else
    echo -e "${RED}✗ test_bot_dca.py not found${NC}"
fi
echo ""

# Test 2: update_linky_history.py
echo -e "${YELLOW}2/4 Testing update_linky_history.py...${NC}"
if [ -f "$HOME/sonoff-energy/test_update_linky_history.py" ]; then
    cd "$HOME/sonoff-energy"
    pytest test_update_linky_history.py -v --cov=update_linky_history --cov-report=json:"$RESULTS_DIR/linky_coverage.json" 2>&1 | tee "$RESULTS_DIR/linky_tests.log" || true
    echo -e "${GREEN}✓ update_linky_history.py tests completed${NC}"
else
    echo -e "${RED}✗ test_update_linky_history.py not found${NC}"
fi
echo ""

# Test 3: app.py
echo -e "${YELLOW}3/4 Testing app.py...${NC}"
if [ -f "$HOME/test_app.py" ]; then
    cd "$HOME"
    pytest test_app.py -v --cov=app --cov-report=json:"$RESULTS_DIR/app_coverage.json" 2>&1 | tee "$RESULTS_DIR/app_tests.log" || true
    echo -e "${GREEN}✓ app.py tests completed${NC}"
else
    echo -e "${RED}✗ test_app.py not found${NC}"
fi
echo ""

# Test 4: aggregator.js
echo -e "${YELLOW}4/4 Testing aggregator.js...${NC}"
if [ -f "$HOME/test_aggregator.js" ]; then
    cd "$HOME"
    npm test -- test_aggregator.js 2>&1 | tee "$RESULTS_DIR/aggregator_tests.log" || true
    echo -e "${GREEN}✓ aggregator.js tests completed${NC}"
else
    echo -e "${RED}✗ test_aggregator.js not found${NC}"
fi
echo ""

# Summary
echo "=============================="
echo -e "${GREEN}✅ Test Suite Execution Complete${NC}"
echo "=============================="
echo ""
echo "📊 Results Summary:"
echo "  - Bot DCA results: $RESULTS_DIR/bot_dca_tests.log"
echo "  - Linky results: $RESULTS_DIR/linky_tests.log"
echo "  - App results: $RESULTS_DIR/app_tests.log"
echo "  - Aggregator results: $RESULTS_DIR/aggregator_tests.log"
echo ""
echo "📈 Coverage Reports:"
echo "  - Bot DCA coverage: $RESULTS_DIR/bot_dca_coverage.json"
echo "  - Linky coverage: $RESULTS_DIR/linky_coverage.json"
echo "  - App coverage: $RESULTS_DIR/app_coverage.json"
echo ""
echo "💡 To view HTML coverage report:"
echo "  pytest --cov=. --cov-report=html"
echo "  Then open htmlcov/index.html"
echo ""

# Check if all tests passed
if grep -q "failed" "$RESULTS_DIR"/*.log 2>/dev/null; then
    echo -e "${RED}⚠️ Some tests may have failed. Check logs above.${NC}"
    exit 1
else
    echo -e "${GREEN}✨ All tests appear to have passed!${NC}"
fi
