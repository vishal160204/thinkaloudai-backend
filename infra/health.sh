#!/bin/bash
# ============================================
# ThinkAloud.ai — Health Check
# Checks ALL services are running
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🏥 ThinkAloud.ai — Health Check"
echo "================================"

check() {
    local name=$1
    local url=$2
    if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC} — $url"
    else
        echo -e "${RED}❌ $name${NC} — $url (DOWN)"
    fi
}

check_service() {
    local name=$1
    if systemctl is-active --quiet "$name" 2>/dev/null; then
        echo -e "${GREEN}✅ $name${NC} — systemd (running)"
    else
        echo -e "${RED}❌ $name${NC} — systemd (stopped)"
    fi
}

check_docker() {
    local name=$1
    if docker ps --format '{{.Names}}' | grep -q "^${name}$" 2>/dev/null; then
        echo -e "${GREEN}✅ $name${NC} — docker (running)"
    else
        echo -e "${RED}❌ $name${NC} — docker (stopped)"
    fi
}

echo ""
echo "── System Services ──"
check_service "postgresql"
check_service "redis"
check_service "thinkaloud"

echo ""
echo "── Docker Containers ──"
check_docker "vllm-llm"
check_docker "vllm-stt"
check_docker "vllm-tts"
check_docker "livekit-server"
check_docker "qdrant"
check_docker "voice-agent"

echo ""
echo "── HTTP Endpoints ──"
check "Backend API"     "http://localhost:8080/health"
check "vLLM LLM"       "http://localhost:8000/health"
check "vLLM STT"       "http://localhost:8001/health"
check "vLLM TTS"       "http://localhost:8002/health"
check "Qdrant"          "http://localhost:6333/healthz"

echo ""
echo "── GPU Info ──"
if command -v rocm-smi &> /dev/null; then
    rocm-smi --showuse --showmemuse 2>/dev/null | head -20
else
    echo -e "${YELLOW}⚠️  rocm-smi not found${NC}"
fi

echo ""
echo "── Disk & Memory ──"
echo "RAM: $(free -h | awk '/^Mem:/{print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $3 "/" $2 " (" $5 " used)"}')"
echo ""
