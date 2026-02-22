"""
ThinkAloud.ai — LLM Service
vLLM API calls for code feedback, hints, and analysis.
All config from settings — zero hardcoded values.
"""
import json
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1024,
    stream: bool = False,
) -> str:
    """Call vLLM chat completions API."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.vllm_base_url}/chat/completions",
                json={
                    "model": settings.vllm_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream,
                    # Disable Qwen3 thinking mode for fast, direct responses
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"LLM API error: {e}", exc_info=True)
        return f"AI feedback unavailable: {str(e)}"


async def generate_code_feedback(
    code: str,
    language: str,
    problem_title: str,
    problem_description: str,
    tests_passed: int,
    tests_total: int,
) -> dict:
    """Generate AI feedback on a code submission."""
    messages = [
        {
            "role": "system",
            "content": """You are a senior software engineer and coding interview evaluator at ThinkAloud.ai.

YOUR ROLE: Analyze the candidate's code submission and provide structured, actionable feedback.

EVALUATION CRITERIA:
1. **Correctness** — Does it handle all cases? Edge cases? Boundary conditions?
2. **Time Complexity** — Big-O analysis of the algorithm
3. **Space Complexity** — Memory usage analysis
4. **Code Quality** — Readability, naming, structure, idiomatic usage
5. **Optimization** — Could it be faster or use less memory?

TONE: Professional, encouraging, specific. Praise what's good, be direct about what's not.

RESPONSE FORMAT — Reply with ONLY this JSON (no markdown, no extra text):
{
    "overall_score": <1-10>,
    "time_complexity": "O(...)",
    "space_complexity": "O(...)",
    "strengths": ["specific strength 1", "specific strength 2"],
    "weaknesses": ["specific weakness 1", "specific weakness 2"],
    "suggestions": ["actionable suggestion 1", "actionable suggestion 2"],
    "summary": "2-3 sentence assessment"
}"""
        },
        {
            "role": "user",
            "content": f"""Problem: {problem_title}
Description: {problem_description}

Language: {language}
Tests Passed: {tests_passed}/{tests_total}

Code:
```{language}
{code}
```

Evaluate this submission."""
        },
    ]

    response = await chat_completion(messages, temperature=0.3, max_tokens=512)

    # Parse JSON from response
    try:
        # Strip markdown code blocks if present
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0]
        return json.loads(cleaned.strip())
    except (json.JSONDecodeError, IndexError):
        logger.warning("Failed to parse LLM feedback as JSON")
        return {
            "overall_score": 0,
            "time_complexity": "Unknown",
            "space_complexity": "Unknown",
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "summary": response[:500],
        }


async def generate_hint(
    problem_title: str,
    problem_description: str,
    user_code: str,
    language: str,
) -> str:
    """Generate a single hint for a stuck user. Never reveal the solution."""
    messages = [
        {
            "role": "system",
            "content": """You are a coding mentor at ThinkAloud.ai. A student is stuck on a problem.

RULES:
- Give exactly ONE small, progressive hint
- NEVER write code, pseudocode, or reveal the algorithm
- NEVER mention the solution approach directly
- Be Socratic — ask a guiding question that leads them toward the insight
- Keep it to 1-2 sentences maximum
- Reference what they've already written to show you understand their attempt

GOOD HINT: "What data structure lets you check if you've seen a number before in O(1) time?"
BAD HINT: "Use a hashmap to store complements." (too direct)"""
        },
        {
            "role": "user",
            "content": f"""Problem: {problem_title}
Description: {problem_description}

Their current code ({language}):
```{language}
{user_code}
```

Give me a hint."""
        },
    ]

    return await chat_completion(messages, temperature=0.5, max_tokens=150)
