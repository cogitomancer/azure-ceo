#!/bin/bash
# Helper script to run test_live_azure.py with proper venv activation

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Checking virtual environment...${NC}"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please create one with: python3 -m venv venv"
    exit 1
fi

# Activate venv and run script
echo -e "${GREEN}✓ Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${GREEN}✓ Running Azure configuration test...${NC}"
echo ""
python scripts/test_live_azure.py

# Deactivate is automatic when script ends
