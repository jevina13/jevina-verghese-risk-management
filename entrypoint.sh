#!/bin/bash
set -e

echo "📥 Loading initial data…"
python load_data.py

echo "🚀 Starting Risk Signal Service…"
uvicorn app.main:app --host 0.0.0.0 --port 8000
