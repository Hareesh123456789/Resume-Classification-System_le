"""
Generic Skills Extractor
------------------------

Detects skills using every JSON file inside:

backend/knowledge/skills/

Features:
- Category-based skill extraction
- Case-insensitive matching
- Common spelling variation support
- Duplicate removal
- Overlapping-match resolution
- Protection against partial-word matches
- Match evidence for explainable results
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Pattern

from utils.knowledge_loader import load_all_skills


# ---------------------------------------------------------
# Common resume spelling variations
# ---------------------------------------------------------

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "javascript": (
        "java script",
    ),
    "typescript": (
        "type script",
    ),
    "node.js": (
        "nodejs",
        "node js",
    ),
    "react.js": (
        "reactjs",
        "react js",
    ),
    "vue.js": (
        "vuejs",
        "vue js",
    ),
    "next.js": (
        "nextjs",
        "next js",
    ),
    "nuxt.js": (
        "nuxtjs",
        "nuxt js",
    ),
    "express.js": (
        "expressjs",
        "express js",
    ),
    "angularjs": (
        "angular js",
    ),
    "asp.net": (
        "asp net",
    ),
    "asp.net core": (
        "asp net core",
    ),
    "vb.net": (
        "vb net",
    ),
    "scikit-learn": (
        "scikit learn",
        "sklearn",
    ),
    "hugging face": (
        "huggingface",
    ),
    "xgboost": (
        "xg boost",
    ),
    "lightgbm": (
        "light gbm",
    ),
    "catboost": (
        "cat boost",
    ),
    "opencv": (
        "open cv",
    ),
    "pytorch": (
        "py torch",
    ),
    "tensorflow": (
        "tensor flow",
    ),
    "mongodb": (
        "mongo db",
    ),
    "postgresql": (
        "postgres sql",
        "postgres",
    ),
    "mysql": (
        "my sql",
    ),
    "sqlite": (
        "sql lite",
    ),
    "github": (
        "git hub",
    ),
    "gitlab": (
        "git lab",
    ),
    "visual studio code": (
        "vs code",
        "vscode",
    ),
    "power bi": (
        "powerbi",
    ),
    "raspberry pi": (
        "raspberrypi",
    ),
    "serviceNow".casefold(): (
        "service now",
    ),
    "object-oriented programming": (
        "object oriented programming",
    ),
    "retrieval-augmented generation": (
        "retrieval augmented generation",
    ),
    "test-driven development": (
        "test driven development",
    ),
    "behavior-driven development": (
        "behaviour driven development",
        "behavior driven development",
    ),
}


# ---------------------------------------------------------
# Internal models
# ---------------------------------------------------------

@dataclass(frozen=True)
class CompiledSkill:
    name: str
    category: str
    pattern: Pattern[str]


@dataclass(frozen=True)
class SkillMatch:
    name: str
    category: str
    matched_text: str
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


# ---------------------------------------------------------
# Text normalization
# ---------------------------------------------------------

def _normalize_text(text: str) -> str:
    """
    Normalize Unicode characters without removing line breaks.
    """

    normalized = unicodedata.normalize("NFKC", text)

    replacements = {
        "\u00a0": " ",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }

    for old_character, new_character in replacements.items():
        normalized = normalized.replace(
            old_character,
            new_character,
        )

    return normalized


# ---------------------------------------------------------
# Pattern construction
# ---------------------------------------------------------

def _create_term_pattern(term: str) -> str:
    """
    Convert a skill name into a safe regular expression.

    Examples:
        "JavaScript" -> JavaScript
        "Java Script" -> Java\\s+Script
        "C++" -> C\\+\\+
    """

    cleaned_term = " ".join(term.split())

    escaped_term = re.escape(cleaned_term)

    # Allow one or more spaces where the knowledge-base
    # term contains a normal space.
    escaped_term = escaped_term.replace(
        r"\ ",
        r"\s+",
    )

    return (
        rf"(?<![A-Za-z0-9])"
        rf"{escaped_term}"
        rf"(?![A-Za-z0-9])"
    )


@lru_cache(maxsize=1)
def _compile_skill_patterns() -> tuple[CompiledSkill, ...]:
    """
    Load the knowledge base and compile searchable patterns.
    """

    knowledge_base = load_all_skills()

    compiled_skills: list[CompiledSkill] = []

    for category, skills in knowledge_base.items():

        for skill_name in skills:

            aliases = SKILL_ALIASES.get(
                skill_name.casefold(),
                (),
            )

            search_terms = {
                skill_name,
                *aliases,
            }

            term_patterns = [
                _create_term_pattern(term)
                for term in sorted(
                    search_terms,
                    key=len,
                    reverse=True,
                )
            ]

            combined_pattern = "|".join(term_patterns)

            compiled_skills.append(
                CompiledSkill(
                    name=skill_name,
                    category=category,
                    pattern=re.compile(
                        combined_pattern,
                        flags=re.IGNORECASE,
                    ),
                )
            )

    return tuple(compiled_skills)


# ---------------------------------------------------------
# Match collection
# ---------------------------------------------------------

def _collect_matches(text: str) -> list[SkillMatch]:
    """
    Find all possible skills before resolving overlaps.
    """

    matches: list[SkillMatch] = []

    for compiled_skill in _compile_skill_patterns():

        for regex_match in compiled_skill.pattern.finditer(text):

            matches.append(
                SkillMatch(
                    name=compiled_skill.name,
                    category=compiled_skill.category,
                    matched_text=regex_match.group(0),
                    start=regex_match.start(),
                    end=regex_match.end(),
                )
            )

    return matches


def _spans_overlap(
    first_match: SkillMatch,
    second_match: SkillMatch,
) -> bool:
    """
    Return True when two matches overlap.
    """

    return (
        first_match.start < second_match.end
        and second_match.start < first_match.end
    )


def _same_span(
    first_match: SkillMatch,
    second_match: SkillMatch,
) -> bool:
    """
    Exact same text span may belong to multiple categories.

    Example:
        Firebase may appear in databases and mobile.
    """

    return (
        first_match.start == second_match.start
        and first_match.end == second_match.end
    )


def _resolve_overlapping_matches(
    matches: list[SkillMatch],
) -> list[SkillMatch]:
    """
    Prefer longer matches.

    Examples:
        C++ is preferred over C.
        Spring Boot is preferred over Spring.
        Oracle Database is preferred over Oracle.
        React.js is preferred over React.
    """

    ordered_matches = sorted(
        matches,
        key=lambda item: (
            -item.length,
            item.start,
            item.category,
            item.name.casefold(),
        ),
    )

    selected_matches: list[SkillMatch] = []

    for candidate in ordered_matches:

        should_skip = False

        for selected in selected_matches:

            if not _spans_overlap(candidate, selected):
                continue

            # Allow the same text span in different categories.
            if _same_span(candidate, selected):
                continue

            should_skip = True
            break

        if not should_skip:
            selected_matches.append(candidate)

    return sorted(
        selected_matches,
        key=lambda item: (
            item.start,
            item.category,
            item.name.casefold(),
        ),
    )


# ---------------------------------------------------------
# Public functions
# ---------------------------------------------------------

def extract_skill_matches(text: str) -> list[dict[str, object]]:
    """
    Return detailed skill matches.

    This will later be useful for:
    - Scoring explanations
    - Debugging
    - Highlighting skills in the frontend
    """

    if not isinstance(text, str):
        raise TypeError(
            "Skills extractor input must be a string."
        )

    if not text.strip():
        return []

    normalized_text = _normalize_text(text)

    possible_matches = _collect_matches(normalized_text)

    resolved_matches = _resolve_overlapping_matches(
        possible_matches
    )

    unique_matches: list[SkillMatch] = []
    seen_matches: set[tuple[str, str]] = set()

    for match in resolved_matches:

        unique_key = (
            match.category.casefold(),
            match.name.casefold(),
        )

        if unique_key in seen_matches:
            continue

        seen_matches.add(unique_key)
        unique_matches.append(match)

    return [
        {
            "name": match.name,
            "category": match.category,
            "matched_text": match.matched_text,
            "start": match.start,
            "end": match.end,
        }
        for match in unique_matches
    ]


def extract_skills(text: str) -> dict[str, list[str]]:
    """
    Extract skills grouped by category.

    Example output:

    {
        "programming_languages": [
            "C++",
            "Python",
            "JavaScript"
        ],
        "databases": [
            "Oracle"
        ],
        "web_technologies": [
            "HTML",
            "CSS"
        ],
        "concepts": [
            "DSA"
        ]
    }
    """

    if not isinstance(text, str):
        raise TypeError(
            "Skills extractor input must be a string."
        )

    knowledge_base = load_all_skills()

    result: dict[str, list[str]] = {
        category: []
        for category in knowledge_base
    }

    if not text.strip():
        return result

    matches = extract_skill_matches(text)

    for match in matches:

        category = str(match["category"])
        skill_name = str(match["name"])

        if skill_name not in result[category]:
            result[category].append(skill_name)

    return result


def clear_skill_extractor_cache() -> None:
    """
    Clear compiled skill patterns after editing JSON files
    in a running Python process.
    """

    _compile_skill_patterns.cache_clear()