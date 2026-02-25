#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# GovPreneurs Auto-Proposal — Local Development Setup Script
# Run: bash setup.sh
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

echo "🏛️  GovPreneurs Auto-Proposal — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Check prerequisites ─────────────────────────────────────────────────────
echo "▶  Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }
command -v node    >/dev/null 2>&1 || { echo "❌ Node.js 18+ required"; exit 1; }
command -v docker  >/dev/null 2>&1 || { echo "⚠️  Docker not found — you'll need to run PostgreSQL/Redis manually"; }

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   Python: $PYTHON_VERSION"
echo "   Node:   $(node --version)"

# ── 2. Create virtual environment ─────────────────────────────────────────────
echo ""
echo "▶  Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r backend/requirements.txt --quiet
echo "   ✅ Python dependencies installed"

# ── 3. Install frontend dependencies ──────────────────────────────────────────
echo ""
echo "▶  Installing frontend dependencies..."
cd frontend && npm install --legacy-peer-deps --silent
cd ..
echo "   ✅ Node.js dependencies installed"

# ── 4. Copy .env.example to .env ──────────────────────────────────────────────
echo ""
if [ ! -f .env ]; then
    cp .env.example .env
    echo "▶  Created .env from .env.example"
    echo "   ⚠️  Edit .env and fill in your API keys before starting!"
else
    echo "▶  .env already exists, skipping"
fi

# ── 5. Start infrastructure with Docker ───────────────────────────────────────
echo ""
echo "▶  Starting PostgreSQL (pgvector) and Redis with Docker..."
docker compose up -d postgres redis || {
    echo "   ⚠️  Docker unavailable. Start PostgreSQL and Redis manually."
}
sleep 3

# ── 6. Run migrations ─────────────────────────────────────────────────────────
echo ""
echo "▶  Running database migrations..."
PYTHONPATH=. alembic upgrade head
echo "   ✅ Database schema created"

# ── 7. Done ───────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅  Setup complete! Start the app with:"
echo ""
echo "   Backend API:     uvicorn backend.main:app --reload"
echo "   Celery worker:   celery -A backend.workers.celery_app worker -l info"
echo "   Celery beat:     celery -A backend.workers.celery_app beat -l info"
echo "   Frontend:        cd frontend && npm run dev"
echo ""
echo "   Or use Docker:   docker compose up"
echo ""
echo "   Open: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
