"""
Catalog search and scoring logic for the SHL Assessment Recommender.

Uses TF-IDF cosine similarity as the base score with keyword and test-type boosting.
Modify this file to add FAISS/vector embeddings or additional filters.
"""
import re
from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ── Test type alias map ───────────────────────────────────────────────────────
# Maps natural language terms to SHL test type codes/labels for boosting
TEST_TYPE_ALIASES: Dict[str, List[str]] = {
    "personality": ["P", "Personality", "Behaviour", "Behavioral"],
    "behaviour": ["P", "Personality", "Behaviour"],
    "behavior": ["P", "Personality", "Behaviour"],
    "cognitive": ["A", "Cognitive", "Ability", "Reasoning"],
    "ability": ["A", "Cognitive", "Ability", "Reasoning"],
    "reasoning": ["A", "Cognitive", "Ability", "Reasoning"],
    "aptitude": ["A", "Cognitive", "Ability"],
    "technical": ["K", "Knowledge", "Skills"],
    "skills": ["K", "Knowledge", "Skills"],
    "knowledge": ["K", "Knowledge", "Skills"],
    "coding": ["K", "Knowledge", "Skills"],
    "programming": ["K", "Knowledge", "Skills"],
    "situational": ["S", "Situational", "Judgment"],
    "judgment": ["S", "Situational", "Judgment"],
    "judgement": ["S", "Situational", "Judgment"],
}

# ── High-value keyword boosts ─────────────────────────────────────────────────
KEYWORD_BOOST_MAP: Dict[str, float] = {
    "java": 0.3,
    "python": 0.3,
    "javascript": 0.3,
    "sql": 0.3,
    "c++": 0.3,
    ".net": 0.3,
    "excel": 0.3,
    "agile": 0.2,
    "scrum": 0.2,
    "leadership": 0.2,
    "sales": 0.2,
    "graduate": 0.2,
    "customer service": 0.2,
    "contact center": 0.2,
    "frontend": 0.2,
    "backend": 0.2,
    "full stack": 0.2,
    "full-stack": 0.2,
    "numerical": 0.2,
    "verbal": 0.2,
    "inductive": 0.2,
    "deductive": 0.2,
    "mechanical": 0.2,
    "spatial": 0.2,
    "safety": 0.15,
    "manufacturing": 0.15,
    "retail": 0.15,
    "admin": 0.15,
    "administrative": 0.15,
    "data entry": 0.15,
    "finance": 0.15,
    "accounting": 0.15,
}


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def item_to_document(item: Dict[str, Any]) -> str:
    """Convert a catalog item to a single searchable text document."""
    parts = [
        item.get("name", ""),
        item.get("test_type", ""),
        item.get("description", ""),
        " ".join(item.get("skills", [])),
        " ".join(item.get("job_family", [])),
        item.get("duration", ""),
    ]
    return " ".join(str(p) for p in parts if p)


class CatalogRetriever:
    """TF-IDF based retriever over the SHL catalog with keyword and type boosting."""

    def __init__(self, catalog: List[Dict[str, Any]]):
        self.catalog = catalog

        if not catalog:
            raise ValueError("Catalog is empty — cannot initialize retriever.")

        self.documents = [item_to_document(item) for item in catalog]

        # Fit TF-IDF on catalog documents
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(self.documents)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search the catalog for items matching the query.

        Scoring:
          base_score  = TF-IDF cosine similarity
          + keyword boost for exact token matches
          + test type boost when user mentions a type category

        Returns up to `limit` results sorted by final score descending.
        """
        if not query.strip():
            return []

        # Base TF-IDF similarity
        try:
            query_vector = self.vectorizer.transform([query])
        except Exception:
            return []

        base_scores = cosine_similarity(query_vector, self.matrix).flatten()
        query_norm = normalize(query)
        boosted: List[tuple] = []

        for idx, base_score in enumerate(base_scores):
            item = self.catalog[idx]
            doc_norm = normalize(item_to_document(item))
            boost = 0.0

            # ── Keyword boost ──
            for keyword, kboost in KEYWORD_BOOST_MAP.items():
                if keyword in query_norm and keyword in doc_norm:
                    boost += kboost

            # ── Test type boost ──
            for phrase, aliases in TEST_TYPE_ALIASES.items():
                if phrase in query_norm:
                    item_type_norm = normalize(item.get("test_type", ""))
                    if any(
                        normalize(alias) in item_type_norm or normalize(alias) in doc_norm
                        for alias in aliases
                    ):
                        boost += 0.25
                        break  # Only boost once per item even if multiple phrases match

            # ── Token overlap boost (for rare/short queries) ──
            for token in re.findall(r"[a-zA-Z0-9+#.]{3,}", query_norm):
                if token in doc_norm:
                    boost += 0.04

            final_score = float(base_score) + boost
            boosted.append((idx, final_score))

        # Sort descending, filter zero-score items
        boosted.sort(key=lambda x: x[1], reverse=True)
        results: List[Dict[str, Any]] = []

        for idx, score in boosted[:limit]:
            if score <= 0:
                continue
            item = dict(self.catalog[idx])
            item["_score"] = round(score, 4)
            results.append(item)

        return results
