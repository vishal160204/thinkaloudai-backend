#!/bin/bash
# ============================================
# ThinkAloud.ai — Restart Services
# Usage: ./restart.sh [service|all]
# ============================================

set -e

SERVICE=${1:-"all"}

restart_backend() {
    echo "🔄 Restarting backend..."
    sudo systemctl restart thinkaloud
    echo "✅ Backend restarted"
}

restart_gpu() {
    echo "🔄 Restarting GPU services (vLLM + LiveKit + Qdrant + Agent)..."
    cd /root/ThinkAloud.ai/infra
    docker compose -f docker-compose.mi300x.yml down
    docker compose -f docker-compose.mi300x.yml up -d
    echo "✅ GPU services restarted"
}

deploy() {
    echo "🚀 Deploying latest code..."
    cd /root/ThinkAloud.ai
    git fetch origin main
    git reset --hard origin/main

    echo "📦 Installing dependencies..."
    cd backend
    ~/.local/bin/uv sync

    echo "🗄️ Running migrations..."
    ~/.local/bin/uv run alembic upgrade head

    echo "🔄 Restarting backend..."
    sudo systemctl restart thinkaloud

    echo "✅ Deploy complete!"
}

case $SERVICE in
    backend)
        restart_backend
        ;;
    gpu)
        restart_gpu
        ;;
    deploy)
        deploy
        ;;
    all)
        deploy
        restart_gpu
        ;;
    *)
        echo "Usage: ./restart.sh [backend|gpu|deploy|all]"
        echo ""
        echo "  backend  — Restart FastAPI only"
        echo "  gpu      — Restart vLLM + LiveKit + Qdrant + Agent"
        echo "  deploy   — Pull code + install deps + migrate + restart backend"
        echo "  all      — Deploy + restart everything"
        ;;
esac
