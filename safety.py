from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a home repair safety classifier. Your job is to classify home repair questions into one of three safety tiers.

Tier definitions:
- safe: Routine maintenance or repair with basic tools where the worst-case outcome is cosmetic damage or a broken fixture — no risk of fire, flooding, injury, or structural failure.
- caution: Repairs involving water or electrical systems that a motivated homeowner can complete, but where mistakes have real cost — bad wiring trips a breaker, a bad connection causes a leak — not catastrophic or life-threatening.
- refuse: Any repair where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death, or where local codes require a licensed professional and a permit.

Critical boundary rule:
If the repair goes wrong and the realistic worst case is fire, flooding, structural failure, injury, or death → refuse. If the worst case is a tripped breaker, a leaky fitting, or a broken fixture → caution.

Respond in exactly this format with no other text:
Tier: [safe|caution|refuse]
Reason: [one sentence explaining why]"""
 
USER_PROMPT_TEMPLATE = """Classify this home repair question:
 
First, think through what this repair actually requires (not how the user framed it). 
Then apply the caution/refuse boundary rule. Then output your answer.
 
Question: {question}"""
 
 
def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.
 
    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned
    """
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(question=question)},
            ],
            temperature=0.0,
            max_tokens=150,
        )
 
        raw = response.choices[0].message.content.strip()
        tier, reason = _parse_response(raw)
        return {"tier": tier, "reason": reason}
 
    except Exception:
        return {
            "tier": "caution",
            "reason": "Classification unavailable; defaulting to caution.",
        }
 
 
def _parse_response(raw: str) -> tuple[str, str]:
    """Parse tier and reason from LLM response. Falls back to caution on failure."""
    tier = "caution"
    reason = "Could not parse classification response."
 
    for line in raw.splitlines():
        line = line.strip()
        if line.lower().startswith("tier:"):
            candidate = line.split(":", 1)[1].strip().lower().rstrip(".")
            if candidate in VALID_TIERS:
                tier = candidate
        elif line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()
 
    return tier, reason
 