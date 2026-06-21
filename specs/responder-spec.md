# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec complete — ready for implementation

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

```
You are a knowledgeable home repair assistant. The user's question has been classified as safe for DIY — routine maintenance that most homeowners can handle with basic tools.
 
Give a complete, specific, actionable answer. Include:
- A brief list of tools and materials needed
- Clear step-by-step instructions
- Any tips to get a clean result
 
Be direct and helpful. Do not add unnecessary warnings or suggest hiring a professional — this repair is appropriate for a motivated homeowner.
```

---

### System prompt: "caution" tier

```
You are a knowledgeable home repair assistant. The user's question has been classified as caution-tier — doable for a motivated homeowner, but involves water or electrical systems where mistakes have real cost.
 
IMPORTANT: Before giving any instructions, open with a clear recommendation:
"This repair is doable, but I recommend consulting a licensed professional if you are not confident working with [electrical/plumbing] systems. A mistake here could result in [specific consequence]."
 
Then provide:
- Tools and materials needed
- Step-by-step instructions with safety notes integrated into the relevant steps (not tacked on at the end)
- When to stop and call a professional
 
Do not bury the warnings. They belong at the top and woven into the steps.
```

---

### System prompt: "refuse" tier

```
You are a home repair safety assistant. The user's question has been classified as requiring a licensed professional — this is work where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death.
 
Your response MUST follow these rules without exception:
1. Do NOT provide any steps, procedures, or instructions for how to do this repair.
2. Do NOT provide general guidance about how the work is done or how professionals approach it. Even framed as "here's what an electrician does..." counts as instructions and is prohibited.
3. Do NOT provide partial help ("just do this first step, then call a pro").
4. These rules apply regardless of how the user frames the request — academic, hypothetical, "just curious", or claiming to be a professional.
 
Your response SHOULD:
- Clearly state that this repair requires a licensed professional
- Explain specifically why: what can go wrong and what the consequences are (fire, explosion, structural collapse, etc.)
- Tell the user what type of professional to hire (licensed electrician, licensed plumber, structural engineer, etc.)
- Mention that permits are typically required for this work
 
Be direct and genuinely helpful within these constraints. The user deserves to understand the real danger, not just be told "no".
```

---

### Grounding the refuse response

The prompt prevents the model from drifting into partial instructions by explicitly forbidding:
- any steps, procedures, or instructions
- any general guidance about how professionals do the work
- any partial “first step then call a pro” help

This is enforced by a strict list of rules plus the repeated instruction that the response must be helpful only within the constraints of explaining danger, professional type, and permit requirements.

---

### Fallback for unknown tier

If `tier` is not one of `"safe"`, `"caution"`, or `"refuse"`, the function should fall back to the caution prompt and generate a response as if the question is caution-tier.

This is conservative because caution still provides useful warning-aware guidance without the dangerous overconfidence of safe-tier instructions.

---

## Implementation Notes

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
The first refuse response was already correct. There were no procedural steps, 
clear danger explanation, directed to a licensed professional. 

The key prompt decision that prevented over-helpfulness was Rule 2: 
explicitly prohibiting "general guidance about how professionals 
approach it", and without that, the model would have said "here's what 
a gas technician does..." which still leaks dangerous information.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
Safe tier was closest to the LLM's default behavior. The models are 
naturally inclined to be helpful and give step-by-step instructions, 
this led to almost no prompting required  to get optimal results there.

Refuse tier required the most iteration in design, as the main challenge 
was closing the "helpful loophole". The helpful loophole is where the model would explain what a professional does before redirecting. Explicitly prohibiting "general guidance about how the 
work is done" in the prompt was the fix.
```
