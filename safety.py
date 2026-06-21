from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """You are a home repair safety classifier. Your job is to classify 
home repair questions into one of three safety tiers.
 
Tier definitions:
- safe: Routine maintenance with basic tools where the worst-case outcome is cosmetic 
  damage or a broken fixture. No risk of fire, flooding, injury, or structural failure.
- caution: Repairs involving water or electrical systems that a motivated homeowner can 
  complete, but where mistakes have real cost. Worst case is a tripped breaker, a leaky 
  fitting, or a broken fixture — not catastrophic or life-threatening.
- refuse: Repairs where an amateur mistake can cause fire, flooding, structural collapse, 
  serious injury, or death. Also includes work requiring a licensed professional and permit.
 
Critical boundary rule:
If the repair goes wrong and the realistic worst case is fire, flooding, structural 
failure, injury, or death → refuse. If the worst case is a tripped breaker or a leaky 
fixture → caution.
 
Key edge cases you MUST apply correctly:
- "Replacing" an existing electrical component (outlet, switch, fixture) at the same 
  location = caution. "Adding new" electrical anywhere (new outlet, new circuit, new 
  switch location) = refuse. These are completely different tiers.
- Any gas line work = always refuse. No exceptions.
- Any wall removal = refuse unless a structural engineer has already confirmed it is 
  non-load-bearing.
- Water heater full replacement = refuse (permit required, pressure relief valve risk). 
  Minor components (anode rod, heating element) = caution.
- "Small" or "minor" framing does not change the tier. Classify based on what the 
  repair actually requires, not how the user describes it.
 
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
        response = _client.chat.completions.create(
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
 