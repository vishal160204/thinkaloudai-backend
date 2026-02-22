"""
ThinkAloud.ai — Voice Interview Agent (MI300X)
LiveKit agent with Mem0 persistent memory.
Remembers user's strengths, weaknesses, and past performance across sessions.

All config via environment variables — zero hardcoded values.
"""
import logging
import os

from livekit.agents import (
    AgentSession, Agent,
    cli, WorkerOptions, JobContext,
)
from livekit.plugins import openai as lk_openai, silero, turn_detector
from mem0 import Memory

logger = logging.getLogger("thinkaloud-agent")

# --- Config from env vars ---
MI300X = os.environ.get("MI300X_URL", "http://localhost")
VLLM_LLM_PORT = os.environ.get("VLLM_LLM_PORT", "8000")
VLLM_STT_PORT = os.environ.get("VLLM_STT_PORT", "8001")
VLLM_TTS_PORT = os.environ.get("VLLM_TTS_PORT", "8002")
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))

LLM_MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen3-32B")
STT_MODEL = os.environ.get("STT_MODEL", "mistralai/Voxtral-Realtime-4B")
TTS_MODEL = os.environ.get("TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B")


# --- Mem0 Setup (local — uses Qdrant + vLLM) ---
mem0_config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": LLM_MODEL,
            "api_key": "not-needed",
            "openai_base_url": f"{MI300X}:{VLLM_LLM_PORT}/v1",
            "temperature": 0.1,
        },
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": LLM_MODEL,
            "api_key": "not-needed",
            "openai_base_url": f"{MI300X}:{VLLM_LLM_PORT}/v1",
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": QDRANT_HOST,
            "port": QDRANT_PORT,
            "collection_name": "thinkaloud_memories",
        },
    },
}

memory = Memory.from_config(mem0_config)


def get_user_memories(user_id: str) -> str:
    """Fetch past memories for this user."""
    try:
        memories = memory.get_all(user_id=user_id)
        if not memories or not memories.get("results"):
            return ""

        memory_lines = [m["memory"] for m in memories["results"][:10]]
        return "\n".join(f"- {m}" for m in memory_lines)
    except Exception as e:
        logger.warning(f"Failed to fetch memories for {user_id}: {e}")
        return ""


def save_conversation_memories(user_id: str, messages: list[dict]):
    """Extract and save important facts from the conversation."""
    try:
        memory.add(messages, user_id=user_id)
        logger.info(f"Saved memories for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to save memories for {user_id}: {e}")


class InterviewerAgent(Agent):
    def __init__(self, problem_context: str = "", user_memories: str = ""):
        memory_section = ""
        if user_memories:
            memory_section = f"""
WHAT YOU REMEMBER ABOUT THIS CANDIDATE (from past sessions):
{user_memories}

Use these memories naturally. For example:
- "Last time you were great with arrays — let's see how you handle this one!"
- "I noticed you've been practicing dynamic programming. Nice progress!"
Do NOT read the memories out loud as a list. Weave them into conversation naturally.
"""

        super().__init__(
            instructions=f"""You are Aria, an AI coding interview coach at ThinkAloud.ai.

PERSONALITY:
- Warm, patient, and genuinely encouraging — like a supportive senior engineer
- You use a conversational, natural tone — NOT robotic or formal
- You celebrate small wins: "Nice catch!" "Exactly right!" "Love that approach!"
- When they struggle, you're empathetic: "That's a tricky part, let's think through it together"
- You have a slight sense of humor — keep it light and professional
- You NEVER sound condescending or patronizing

VOICE STYLE:
- Keep ALL responses to 1-3 sentences. This is a voice conversation, not a lecture.
- Speak naturally — use contractions ("you're", "that's", "let's")
- Avoid code in your speech — describe algorithms in plain English
- Pause for them to think. Don't rush to fill silence.

INTERVIEW RULES:
- Ask the candidate to explain their approach BEFORE they start coding
- If they're stuck, give ONE small Socratic hint — ask a guiding question
- NEVER write code for them. NEVER reveal the solution. NEVER give the algorithm name.
- If they mention a good approach, affirm it and ask them to elaborate
- Ask about time and space complexity AFTER they have a working solution
- If they solve it, congratulate them genuinely and discuss edge cases or optimizations

CONVERSATION FLOW:
1. Greet them warmly and introduce the problem briefly (1-2 sentences)
2. Ask: "Before you start coding, can you walk me through how you'd approach this?"
3. Listen to their approach, ask clarifying questions
4. As they code, check in: "How's it going?" / "Talk me through what you're writing"
5. When done: "Great, let's trace through an example together"
6. Discuss complexity and possible improvements
7. End on a positive note with specific feedback
{memory_section}
{f"PROBLEM CONTEXT:\n{problem_context}" if problem_context else "No problem assigned yet. Ask the user what problem they'd like to work on."}""",
        )


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    # Get problem context and user identity from room
    problem_context = ctx.room.metadata or ""

    # Extract user_id from participant identity (format: "user-{id}")
    user_id = None
    for participant in ctx.room.remote_participants.values():
        if participant.identity.startswith("user-"):
            user_id = participant.identity
            break

    # Fetch memories for this user
    user_memories = ""
    if user_id:
        user_memories = get_user_memories(user_id)
        if user_memories:
            logger.info(f"Loaded {len(user_memories.splitlines())} memories for {user_id}")

    # --- All models on MI300X ---

    # STT: Voxtral Realtime (self-hosted on vLLM)
    stt = lk_openai.STT(
        model=STT_MODEL,
        base_url=f"{MI300X}:{VLLM_STT_PORT}/v1",
        api_key="not-needed",
        language="en",
    )

    # LLM: Qwen3-32B (dense, thinking mode disabled)
    llm = lk_openai.LLM(
        model=LLM_MODEL,
        base_url=f"{MI300X}:{VLLM_LLM_PORT}/v1",
        api_key="not-needed",
        temperature=0.7,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": False},
        },
    )

    # TTS: Qwen3-TTS (streaming)
    tts = lk_openai.TTS(
        model=TTS_MODEL,
        base_url=f"{MI300X}:{VLLM_TTS_PORT}/v1",
        api_key="not-needed",
    )

    # VAD: Silero (CPU, tiny)
    vad = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.4,
        prefix_padding_duration=0.3,
        activation_threshold=0.5,
    )

    session = AgentSession(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
        turn_detection=turn_detector.EOUModel(),
    )

    agent = InterviewerAgent(problem_context, user_memories)

    await session.start(
        room=ctx.room,
        agent=agent,
    )

    # After session ends — save memories
    if user_id and hasattr(session, 'chat_ctx') and session.chat_ctx:
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in session.chat_ctx.messages
            if msg.content
        ]
        save_conversation_memories(user_id, messages)
        logger.info(f"Session ended. Memories saved for {user_id}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
