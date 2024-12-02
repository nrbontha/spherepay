#!/bin/bash

# Start FastAPI in the background
echo "Starting FastAPI server..."
poetry run uvicorn spherepay.main:app --reload &

# Wait for FastAPI to start
sleep 3

# Start FX rates mock script
echo "Starting FX rates mock..."
node scripts/mock_fx_rates.js http://localhost:8000/fx-rate 