#!/bin/bash
set -e

echo "=== Samsung Buzz Analysis Agent Local Runner ==="

# 1. Environment Check
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env-example..."
    cp .env-example .env
    echo "❌ PLEASE EDIT .env with your Google Cloud & BigQuery details before continuing."
    exit 1
fi

# 2. Setup Backend
echo "--> Setting up Backend..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# 3. Build Frontend
echo "--> Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 4. Run Server
echo "--> Starting Agent Server..."
echo "You can access the agent at: http://localhost:8080"
python3 -m uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8080 --reload
