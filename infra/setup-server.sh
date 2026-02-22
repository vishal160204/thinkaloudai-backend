#!/bin/bash
# ============================================
# ThinkAloud.ai — First-Time Server Setup
# Run this ONCE on a fresh MI300X server
# ============================================

set -e

SERVER_IP="134.199.198.184"
REPO_URL="https://github.com/vishal160204/ThinkAloud.ai.git"  # Update with your repo

echo "🔧 ThinkAloud.ai — Server Setup"
echo "================================"
echo "Server: $SERVER_IP"
echo ""

# --- 1. System packages ---
echo "📦 Installing system packages..."
apt update && apt install -y \
  postgresql postgresql-contrib \
  redis-server \
  git \
  curl \
  docker.io \
  docker-compose-plugin

# --- 2. Start system services ---
echo "🔌 Starting system services..."
systemctl enable --now postgresql redis-server docker

# --- 3. Install uv ---
echo "📦 Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# --- 4. Install Python 3.13 ---
echo "🐍 Installing Python 3.13..."
uv python install 3.13

# --- 5. Create database ---
echo "🗄️ Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE USER vishal WITH PASSWORD 'vishal16';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE thinkaloudai OWNER vishal;" 2>/dev/null || true
echo "✅ Database ready"

# --- 6. Clone repo ---
if [ ! -d "/root/ThinkAloud.ai" ]; then
  echo "📥 Cloning repository..."
  cd /root
  git clone "$REPO_URL"
fi

# --- 7. Backend setup ---
echo "📦 Installing backend dependencies..."
cd /root/ThinkAloud.ai/backend
uv sync

# --- 8. Create .env ---
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "⚠️  Created .env from .env.example"
    echo "   Edit it with: nano /root/ThinkAloud.ai/backend/.env"
    echo "   Then run this script again."
    exit 1
  else
    echo "❌ No .env or .env.example found!"
    exit 1
  fi
fi

# --- 9. Run database migrations ---
echo "🗄️ Running migrations..."
uv run alembic upgrade head

# --- 10. Seed problems ---
echo "🌱 Seeding problems..."
uv run python -m scripts.seed || true

# --- 11. Install systemd service ---
echo "⚙️ Installing backend service..."
cp /root/ThinkAloud.ai/infra/thinkaloud.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable thinkaloud
systemctl start thinkaloud

# --- 12. Start GPU services ---
echo "🚀 Starting GPU services (vLLM + LiveKit + Qdrant + Agent)..."
cd /root/ThinkAloud.ai/infra
docker compose -f docker-compose.mi300x.yml up -d

# --- 13. Make scripts executable ---
chmod +x /root/ThinkAloud.ai/infra/*.sh

# --- Done ---
echo ""
echo "============================================"
echo "✅ ThinkAloud.ai — Setup Complete!"
echo "============================================"
echo ""
echo "🌐 Services:"
echo "   Backend:  http://$SERVER_IP:8080/docs"
echo "   Health:   http://$SERVER_IP:8080/health"
echo "   vLLM LLM: http://$SERVER_IP:8000/v1/models"
echo "   vLLM STT: http://$SERVER_IP:8001/v1/models"
echo "   vLLM TTS: http://$SERVER_IP:8002/v1/models"
echo "   LiveKit:  ws://$SERVER_IP:7880"
echo "   Qdrant:   http://$SERVER_IP:6333"
echo ""
echo "🛠️ Commands:"
echo "   ./infra/health.sh     — Check all services"
echo "   ./infra/logs.sh       — View logs"
echo "   ./infra/restart.sh    — Restart services"
echo ""
echo "📋 Next: Push code to GitHub, set up CI/CD secrets"
echo "   After that, every 'git push origin main' auto-deploys!"
echo ""
