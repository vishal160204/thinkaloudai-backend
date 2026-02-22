FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py .

# Defaults — overridden by docker-compose environment section
ENV LIVEKIT_URL=ws://livekit:7880
ENV MI300X_URL=http://host.docker.internal
ENV VLLM_LLM_PORT=8000
ENV VLLM_STT_PORT=8001
ENV VLLM_TTS_PORT=8002
ENV QDRANT_HOST=qdrant
ENV QDRANT_PORT=6333
ENV LLM_MODEL=Qwen/Qwen3-32B
ENV STT_MODEL=mistralai/Voxtral-Realtime-4B
ENV TTS_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B

CMD ["python", "agent.py", "start"]
