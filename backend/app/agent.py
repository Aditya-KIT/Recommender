"""
Conversation behavior brain for the SHL Assessment Recommender.

Responsibilities:
- Vague query detection
- Clarification logic (ask ONE question per turn)
- Comparison behavior (catalog data only)
- Recommendation building (1–10 items)
- End-of-conversation detection
"""
import re
from typing import Any, Dict, List, Tuple

from app.guardrails import is_off_topic, refusal_reply
from app.prompts import VAGUE_QUERY_REPLY, NO_MATCH_REPLY
from app.schemas import ChatMessage, Recommendation
from app.retriever import CatalogRetriever

# ─── Role / domain signals ────────────────────────────────────────────────────
ROLE_WORDS = [
    "developer", "engineer", "java", "python", "sales", "manager", "analyst",
    "support", "graduate", "leadership", "finance", "accounting", "customer",
    "stakeholder", "admin", "backend", "frontend", "full stack", "full-stack",
    "data", "qa", "testing", "devops", "cloud", "product", "marketing",
    "operations", "hr", "recruiter", "designer", "architect", "executive",
    "director", "consultant", "specialist", "coordinator", "associate",
    "intern", "junior", "senior", "mid-level", "entry", "lead", "head",
]

ASSESSMENT_SIGNAL_WORDS = [
    "assess", "assessment", "test", "hire", "hiring", "candidate", "recruit",
    "measure", "evaluate", "skill", "competency", "aptitude", "ability",
    "personality", "cognitive", "recommend", "suggest", "shortlist",
]

COMPARE_WORDS = ["compare", "difference", "vs", "versus", "differ", "contrast", "between"]

VAGUE_EXACT_PATTERNS = [
    r"^i need an assessment$",
    r"^need assessment$",
    r"^recommend assessment[s]?$",
    r"^assessment[s]?$",
    r"^i need a test$",
    r"^suggest tests?$",
    r"^help$",
    r"^hi$",
    r"^hello$",
    r"^hey$",
    r"^what can you do\??$",
]

# ─── Utility helpers ───────────────────────────────────────────────────────────

def flatten_messages(messages: List[ChatMessage]) -> str:
    """Combine all messages into a single context string."""
    return "\n".join(f"{m.role}: {m.content}" for m in messages)


def latest_user_message(messages: List[ChatMessage]) -> str:
    """Return the most recent user message content."""
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


def get_all_user_text(messages: List[ChatMessage]) -> str:
    """Concatenate all user messages for history-based checks."""
    return " ".join(m.content for m in messages if m.role == "user")


# ─── Intent detection ─────────────────────────────────────────────────────────

def is_vague(text: str) -> bool:
    """Return True if the text is too vague to make a recommendation."""
    cleaned = re.sub(r"\s+", " ", text.lower()).strip().rstrip(".!?")

    # Exact vague patterns
    if any(re.match(pattern, cleaned) for pattern in VAGUE_EXACT_PATTERNS):
        return True

    words = cleaned.split()
    # Very short and no role or assessment keyword
    if len(words) < 5:
        has_role = any(word in cleaned for word in ROLE_WORDS)
        has_signal = any(word in cleaned for word in ASSESSMENT_SIGNAL_WORDS)
        return not (has_role or has_signal)

    return False


def needs_clarification(messages: List[ChatMessage]) -> bool:
    """
    Return True if the full conversation history still lacks enough context
    to make a grounded recommendation. Requires at least a role signal.
    """
    full_user_text = get_all_user_text(messages).lower()

    has_role = any(word in full_user_text for word in ROLE_WORDS)
    has_signal = any(word in full_user_text for word in ASSESSMENT_SIGNAL_WORDS)

    # If we have both role and any assessment signal, we have enough context
    return not (has_role and has_signal)


def is_compare_request(text: str) -> bool:
    """Return True if the user is asking to compare assessments."""
    lower = text.lower()
    return any(word in lower for word in COMPARE_WORDS)


# ─── Response builders ─────────────────────────────────────────────────────────

def compare_reply(query: str, retriever: CatalogRetriever) -> str:
    """Build a comparison reply using only catalog data."""
    results = retriever.search(query, limit=5)

    if len(results) < 2:
        return (
            "To compare assessments, I need to identify at least two matching items in the SHL catalog. "
            "Please name the assessments you'd like to compare (e.g., 'Compare OPQ32r and Verify G+ General Ability')."
        )

    lines = []
    for i, item in enumerate(results[:4], start=1):
        name = item.get("name", "Unknown")
        test_type = item.get("test_type", "N/A")
        desc = item.get("description", "No description available.")
        duration = item.get("duration", "Duration not listed")
        skills = ", ".join(item.get("skills", []))
        lines.append(
            f"**{i}. {name}** (Type: {test_type}, {duration})\n"
            f"   {desc}\n"
            f"   Skills: {skills if skills else 'Not listed'}"
        )

    return (
        "Here is a catalog-based comparison of the top matching assessments:\n\n"
        + "\n\n".join(lines)
        + "\n\nWould you like me to narrow this down based on a specific role or skill requirement?"
    )


def build_recommendations(results: List[Dict[str, Any]]) -> List[Recommendation]:
    """Build Recommendation objects from retriever results, deduplicating by URL."""
    recs: List[Recommendation] = []
    seen_urls: set = set()

    for item in results:
        name = item.get("name")
        url = item.get("url")
        test_type = item.get("test_type", "")

        if not name or not url:
            continue
        if url in seen_urls:
            continue

        seen_urls.add(url)
        recs.append(Recommendation(name=name, url=url, test_type=test_type))

        if len(recs) >= 10:
            break

    return recs


def build_reply_text(recs: List[Recommendation], messages: List[ChatMessage]) -> str:
    """Compose a natural reply mentioning the number and type of recommendations."""
    n = len(recs)
    user_text = get_all_user_text(messages).lower()

    # Detect what types are in the results
    types_found = {r.test_type for r in recs}
    type_labels = []
    if "K" in types_found:
        type_labels.append("knowledge/skills")
    if "A" in types_found:
        type_labels.append("cognitive ability")
    if "P" in types_found:
        type_labels.append("personality")
    if "S" in types_found:
        type_labels.append("situational judgment")

    type_str = " and ".join(type_labels) if type_labels else "mixed"

    return (
        f"Based on the role and requirements you described, here {'is' if n == 1 else 'are'} "
        f"{n} SHL {type_str} assessment{'s' if n != 1 else ''} from the catalog that best fit your needs. "
        "You can click any item below to view it in the SHL product catalog."
    )


# ─── Main entry point ─────────────────────────────────────────────────────────

def generate_reply(
    messages: List[ChatMessage], retriever: CatalogRetriever
) -> Tuple[str, List[Recommendation], bool]:
    """
    Core conversation logic.

    Returns:
        (reply_text, recommendations, end_of_conversation)
    """
    if not messages:
        return (
            "Hi! I can help you find the right SHL assessments. "
            "What role are you hiring for, and what would you like to evaluate — "
            "technical skills, cognitive ability, personality, or a combination?",
            [],
            False,
        )

    latest = latest_user_message(messages)
    if not latest:
        return (
            "Could you describe the role or hiring need? I'll match it to SHL catalog assessments.",
            [],
            False,
        )

    # ── Guardrail: off-topic / unsafe ──
    if is_off_topic(latest):
        return refusal_reply(), [], False

    # ── Comparison request ──
    if is_compare_request(latest):
        return compare_reply(latest, retriever), [], False

    # ── Vague single message ──
    if is_vague(latest):
        return VAGUE_QUERY_REPLY, [], False

    # ── Clarification needed (check full history) ──
    if needs_clarification(messages):
        return (
            "Could you tell me more about the role? "
            "Specifically: the job title or area, the skills to assess (technical, cognitive, personality), "
            "and the experience level (entry, mid, senior, or leadership)?",
            [],
            False,
        )

    # ── Retrieve recommendations ──
    full_context = flatten_messages(messages)
    results = retriever.search(full_context, limit=10)
    recs = build_recommendations(results)

    if not recs:
        return NO_MATCH_REPLY, [], False

    reply = build_reply_text(recs, messages)
    return reply, recs, False
