#!/bin/bash
# ============================================
# ThinkAloud.ai — View Logs
# Usage: ./logs.sh [service]
# Examples:
#   ./logs.sh           → all services
#   ./logs.sh backend   → FastAPI logs
#   ./logs.sh llm       → vLLM LLM logs
#   ./logs.sh stt       → vLLM STT logs
#   ./logs.sh tts       → vLLM TTS logs
#   ./logs.sh livekit   → LiveKit logs
#   ./logs.sh agent     → Voice agent logs
#   ./logs.sh qdrant    → Qdrant logs
# ============================================

SERVICE=${1:-"all"}

case $SERVICE in
    backend)
        echo "📋 Backend (FastAPI) logs:"
        journalctl -u thinkaloud -f --no-pager
        ;;
    llm)
        echo "📋 vLLM LLM logs:"
        docker logs -f vllm-llm --tail 100
        ;;
    stt)
        echo "📋 vLLM STT logs:"
        docker logs -f vllm-stt --tail 100
        ;;
    tts)
        echo "📋 vLLM TTS logs:"
        docker logs -f vllm-tts --tail 100
        ;;
    livekit)
        echo "📋 LiveKit logs:"
        docker logs -f livekit-server --tail 100
        ;;
    agent)
        echo "📋 Voice Agent logs:"
        docker logs -f voice-agent --tail 100
        ;;
    qdrant)
        echo "📋 Qdrant logs:"
        docker logs -f qdrant --tail 100
        ;;
    all)
        echo "📋 All service status:"
        echo ""
        echo "── Backend ──"
        journalctl -u thinkaloud --no-pager -n 5
        echo ""
        echo "── Docker ──"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
        echo ""
        echo "Use './logs.sh <service>' for live logs"
        echo "Services: backend, llm, stt, tts, livekit, agent, qdrant"
        ;;
    *)
        echo "Unknown service: $SERVICE"
        echo "Available: backend, llm, stt, tts, livekit, agent, qdrant, all"
        ;;
esac
