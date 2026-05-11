"""
Guardrails for the SHL Assessment Recommender.

Detects:
- Off-topic queries (hiring/legal/salary/resume advice)
- Prompt injection attempts
- General out-of-scope questions

Does NOT block:
- Assessment-related queries even if they use words like "contract" in an HR context
"""
import re

# ── Prompt injection patterns ─────────────────────────────────────────────────
INJECTION_PATTERNS = [
    r"\bignore (previous|all|above|prior) instructions?\b",
    r"\bact as\b",
    r"\bpretend (you are|to be|you're)\b",
    r"\bsystem prompt\b",
    r"\bdeveloper mode\b",
    r"\bjailbreak\b",
    r"\bprompt injection\b",
    r"\byou are now\b",
    r"\bforget (everything|all) (above|previous|prior)\b",
    r"\bdisregard (your|all|previous)\b",
    r"\boverride (your|the) (instructions?|rules?|guidelines?)\b",
]

# ── Off-topic topic patterns ──────────────────────────────────────────────────
OFF_TOPIC_PATTERNS = [
    r"\b(what|how much) (is|are|should) (the )?(salary|pay|wage|compensation|benefits)\b",
    r"\bsalary (range|negotiation|advice)\b",
    r"\bwrite (me )?(a |my )?(resume|cv|cover letter|job description)\b",
    r"\b(how to|tips for) (write|craft|improve) (a )?(resume|cv|cover letter)\b",
    r"\b(is it legal|legal (advice|question|issue|implications?|requirement))\b",
    r"\bdiscrimination law\b",
    r"\bemployment law\b",
    r"\bconsult (a |your )?(lawyer|attorney|legal)\b",
    r"\binterview questions? (to ask|for candidates)\b",
    r"\bhow (do i|to) (pass|cheat|beat|trick) (a |the )?(assessment|test)\b",
    r"\b(what|tell me) (stocks?|crypto|investment|forex)\b",
    r"\bwrite (code|a program|a script) for me\b",
]

# ── SHL-domain terms (allow-list to prevent false positives) ──────────────────
SHL_CONTEXT_TERMS = [
    "shl", "assessment", "test", "candidate", "hiring", "recruit", "developer",
    "java", "python", "sales", "manager", "graduate", "personality", "cognitive",
    "ability", "skills", "technical", "compare", "opq", "verify", "gsa",
    "aptitude", "reasoning", "situational", "job family", "test type",
    "recommendation", "shortlist", "evaluate", "measure",
]


def _matches_any(text: str, patterns: list) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def is_off_topic(text: str) -> bool:
    """
    Return True if the query is clearly off-topic or a prompt injection attempt.
    False positives are minimized by checking for SHL-domain context first for
    borderline cases.
    """
    # Prompt injection is always off-topic, no exceptions
    if _matches_any(text, INJECTION_PATTERNS):
        return True

    # Off-topic topic check — only block if no SHL context is present
    if _matches_any(text, OFF_TOPIC_PATTERNS):
        lowered = text.lower()
        has_shl_context = any(term in lowered for term in SHL_CONTEXT_TERMS)
        return not has_shl_context

    return False


def refusal_reply() -> str:
    return (
        "I can only help you select, refine, or compare SHL Individual Test Solutions from the official catalog. "
        "I'm not able to provide salary guidance, legal advice, resume writing, interview prep tips, "
        "or anything outside of SHL assessment selection."
    )
