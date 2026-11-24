#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " FlagForge Setup & Health Verification"
echo "============================================================"

# Pre-flight check
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH."
    exit 1
fi

if [ ! -f .env ]; then
    echo "📋 Copying .env.example to .env..."
    cp .env.example .env
fi

echo "🚀 Starting FlagForge multi-service stack with Docker Compose..."
docker compose up -d --build

echo "⏳ Polling FlagForge API health at http://localhost:8000/health..."
MAX_RETRIES=30
COUNT=0
while [ $COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ FlagForge API is healthy and operational!"
        break
    fi
    COUNT=$((COUNT+1))
    echo "Waiting for API... ($COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️ Warning: Healthcheck timed out. Check 'docker compose logs api'."
    exit 1
fi

echo ""
echo "============================================================"
echo " FlagForge Stack Running Successfully"
echo "============================================================"
echo "  Web UI:         http://localhost:3000"
echo "  API Docs:       http://localhost:8000/api/v1/docs"
echo "  API Health:     http://localhost:8000/health"
echo "  OTel Collector: http://localhost:4318"
echo "============================================================"
