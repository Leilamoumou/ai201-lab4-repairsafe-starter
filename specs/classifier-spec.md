# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec complete — ready for implementation

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

### Tier definitions

**safe:**
```
Routine maintenance or repair with basic tools where the worst-case outcome is cosmetic damage or a broken fixture — no risk of fire, flooding, injury, or structural failure.
```

**caution:**
```
Repairs involving water or electrical systems that a motivated homeowner can complete, but where mistakes have real cost — bad wiring trips a breaker, a bad connection causes a leak — not catastrophic or life-threatening.
```

**refuse:**
```
Any repair where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death, or where local codes require a licensed professional and a permit.
```

---

### Classification approach

Definitions + chain-of-thought reasoning before naming the tier. The LLM should reason about what the repair actually requires (not how the user frames it), then apply the caution/refuse boundary rule and output the tier.

This approach handles boundary cases more reliably by forcing the model to commit to reasoning first, instead of guessing a label directly.

---

### Output format

The model should return exactly two lines in this format:

```
Tier: safe|caution|refuse
Reason: one sentence
```

Parsing should be simple and strict: split on newlines, find the line starting with `Tier:`, extract the word after the colon, lowercase and strip it, then validate against `VALID_TIERS`.

---

### Prompt structure

**System message:**
```
You are a home repair safety classifier. Your job is to classify home repair questions into one of three safety tiers.

Tier definitions:
- safe: Routine maintenance or repair with basic tools where the worst-case outcome is cosmetic damage or a broken fixture — no risk of fire, flooding, injury, or structural failure.
- caution: Repairs involving water or electrical systems that a motivated homeowner can complete, but where mistakes have real cost — bad wiring trips a breaker, a bad connection causes a leak — not catastrophic or life-threatening.
- refuse: Any repair where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death, or where local codes require a licensed professional and a permit.

Critical boundary rule:
If the repair goes wrong and the realistic worst case is fire, flooding, structural failure, injury, or death → refuse. If the worst case is a tripped breaker, a leaky fitting, or a broken fixture → caution.

Respond in exactly this format with no other text:
Tier: [safe|caution|refuse]
Reason: [one sentence explaining why]
```

**User message:**
```
Classify this home repair question:

First, think through what this repair actually requires (not how the user framed it).
Then apply the caution/refuse boundary rule. Then output your answer.

Question: {question}
```

---

### Caution/refuse boundary

If the repair goes wrong and the realistic worst case is fire, flooding, structural failure, injury, or death — classify it as `refuse`; if the worst case is a tripped breaker, a leaky fitting, or a broken fixture — classify it as `caution`.

Example boundary cases:
- `Can I add a new circuit to my garage?` → `refuse`, because adding new electrical work creates realistic risk of shock, fire, and usually requires licensed/permit-backed work.
- `Can I replace a dead outlet in my kitchen?` → `caution`, because replacing an existing outlet is usually homeowner-level and a mistake is more likely to trip a breaker than cause catastrophe.

---

### Fallback behavior

If the LLM response cannot be parsed or the extracted tier is not one of `VALID_TIERS`, return:
```
{"tier": "caution", "reason": "Classification unavailable; defaulting to caution."}
```

This is conservative: failing open to `safe` is dangerous because it could lead to unsafe DIY instructions, while `caution` avoids dangerous advice and still provides a useful middle ground.

---

## Implementation Notes

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
A classification that surprised me : 

Question: "Can I add a new electrical outlet to my garage?"
Expected: possibly caution (it's just an outlet...)
Returned: refuse — correct, because adding new requires opening 
the panel and running new wire, which is fire-hazard territory.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
Added explicit "replacing existing vs. adding new" language to the 
system prompt after recognizing the classifier needed a concrete rule 
to distinguish component swaps from new electrical infrastructure.

The classifier worked correctly on the first run, and the most important 
prompt decision was explicitly naming the replacing-vs-adding edge case 
rather than leaving it implicit in the tier definitions — without that 
rule, both outlet questions could have landed in caution.
```
