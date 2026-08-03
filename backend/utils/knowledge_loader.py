"""
Knowledge Base Loader
---------------------

Loads and validates all categorized skill JSON files from:

backend/knowledge/skills/

Expected JSON format:

{
    "category": "programming_languages",
    "skills": [
        "Python",
        "Java",
        "C++"
    ]
}
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]

DEFAULT_SKILLS_DIRECTORY = (
    BACKEND_DIRECTORY
    / "knowledge"
    / "skills"
)


# ---------------------------------------------------------
# Custom exception
# ---------------------------------------------------------

class KnowledgeBaseError(Exception):
    """Raised when the knowledge base is missing or invalid."""


# ---------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------

def _validate_category(
    category: Any,
    file_path: Path,
) -> str:
    """
    Validate and clean the category field.
    """

    if not isinstance(category, str):
        raise KnowledgeBaseError(
            f"'category' must be a string in: {file_path.name}"
        )

    cleaned_category = category.strip()

    if not cleaned_category:
        raise KnowledgeBaseError(
            f"'category' cannot be empty in: {file_path.name}"
        )

    return cleaned_category


def _validate_skills(
    skills: Any,
    file_path: Path,
) -> tuple[str, ...]:
    """
    Validate, clean and remove duplicate skills.

    Duplicate checking is case-insensitive.
    Original skill capitalization is preserved.
    """

    if not isinstance(skills, list):
        raise KnowledgeBaseError(
            f"'skills' must be a list in: {file_path.name}"
        )

    cleaned_skills: list[str] = []
    seen_skills: set[str] = set()

    for position, skill in enumerate(skills, start=1):

        if not isinstance(skill, str):
            raise KnowledgeBaseError(
                f"Skill number {position} must be a string "
                f"in: {file_path.name}"
            )

        # Remove leading, trailing and repeated spaces.
        cleaned_skill = " ".join(skill.split())

        if not cleaned_skill:
            continue

        normalized_skill = cleaned_skill.casefold()

        if normalized_skill not in seen_skills:
            cleaned_skills.append(cleaned_skill)
            seen_skills.add(normalized_skill)

    return tuple(cleaned_skills)


def _read_json_file(file_path: Path) -> dict[str, Any]:
    """
    Read one JSON knowledge-base file.
    """

    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as json_file:

            data = json.load(json_file)

    except json.JSONDecodeError as error:
        raise KnowledgeBaseError(
            f"Invalid JSON in {file_path.name}: "
            f"line {error.lineno}, column {error.colno}. "
            f"{error.msg}"
        ) from error

    except OSError as error:
        raise KnowledgeBaseError(
            f"Unable to read {file_path}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise KnowledgeBaseError(
            f"The root JSON value must be an object in: "
            f"{file_path.name}"
        )

    return data


# ---------------------------------------------------------
# Internal cached loader
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def _load_cached_knowledge_base() -> (
    dict[str, tuple[str, ...]]
):
    """
    Load and cache all JSON skill files.

    The internal values are tuples so cached information
    cannot accidentally be changed.
    """

    skills_directory = DEFAULT_SKILLS_DIRECTORY

    if not skills_directory.exists():
        raise KnowledgeBaseError(
            "Skills directory was not found:\n"
            f"{skills_directory}"
        )

    if not skills_directory.is_dir():
        raise KnowledgeBaseError(
            "The skills path is not a directory:\n"
            f"{skills_directory}"
        )

    json_files = sorted(
        skills_directory.glob("*.json")
    )

    if not json_files:
        raise KnowledgeBaseError(
            "No JSON files were found in:\n"
            f"{skills_directory}"
        )

    knowledge_base: dict[str, tuple[str, ...]] = {}
    normalized_categories: set[str] = set()

    for file_path in json_files:

        data = _read_json_file(file_path)

        if "category" not in data:
            raise KnowledgeBaseError(
                f"Missing 'category' field in: "
                f"{file_path.name}"
            )

        if "skills" not in data:
            raise KnowledgeBaseError(
                f"Missing 'skills' field in: "
                f"{file_path.name}"
            )

        category = _validate_category(
            data["category"],
            file_path,
        )

        skills = _validate_skills(
            data["skills"],
            file_path,
        )

        normalized_category = category.casefold()

        if normalized_category in normalized_categories:
            raise KnowledgeBaseError(
                f"Duplicate category '{category}' "
                f"found in: {file_path.name}"
            )

        normalized_categories.add(normalized_category)
        knowledge_base[category] = skills

    return knowledge_base


# ---------------------------------------------------------
# Public functions
# ---------------------------------------------------------

def load_all_skills() -> dict[str, list[str]]:
    """
    Return all skill categories and their skills.

    A fresh dictionary is returned so callers cannot
    modify the cached knowledge base.

    Example:

    {
        "programming_languages": ["Python", "Java"],
        "databases": ["MySQL", "Oracle"]
    }
    """

    cached_data = _load_cached_knowledge_base()

    return {
        category: list(skills)
        for category, skills in cached_data.items()
    }


def load_skill_category(
    category: str,
) -> list[str]:
    """
    Load one skill category.

    Category matching is case-insensitive.

    Example:

    load_skill_category("databases")
    """

    if not isinstance(category, str):
        raise TypeError(
            "Category must be provided as a string."
        )

    requested_category = category.strip().casefold()

    if not requested_category:
        raise ValueError(
            "Category cannot be empty."
        )

    knowledge_base = _load_cached_knowledge_base()

    for stored_category, skills in knowledge_base.items():

        if stored_category.casefold() == requested_category:
            return list(skills)

    available_categories = ", ".join(
        sorted(knowledge_base.keys())
    )

    raise KeyError(
        f"Unknown skill category: '{category}'. "
        f"Available categories: {available_categories}"
    )


@lru_cache(maxsize=1)
def _build_cached_skill_index() -> (
    dict[str, tuple[tuple[str, str], ...]]
):
    """
    Build a normalized searchable index.

    One skill may appear in several categories.

    Example:

    {
        "python": (
            ("Python", "programming_languages"),
        ),
        "firebase": (
            ("Firebase", "databases"),
            ("Firebase", "mobile"),
        )
    }
    """

    knowledge_base = _load_cached_knowledge_base()

    temporary_index: dict[
        str,
        list[tuple[str, str]]
    ] = {}

    for category, skills in knowledge_base.items():

        for skill in skills:

            normalized_skill = skill.casefold()

            entry = (
                skill,
                category,
            )

            temporary_index.setdefault(
                normalized_skill,
                [],
            )

            if entry not in temporary_index[normalized_skill]:
                temporary_index[normalized_skill].append(entry)

    return {
        key: tuple(entries)
        for key, entries in temporary_index.items()
    }


def build_skill_index() -> (
    dict[str, list[dict[str, str]]]
):
    """
    Return a searchable skill index.

    Example:

    {
        "python": [
            {
                "name": "Python",
                "category": "programming_languages"
            }
        ]
    }
    """

    cached_index = _build_cached_skill_index()

    return {
        normalized_skill: [
            {
                "name": skill_name,
                "category": category,
            }
            for skill_name, category in entries
        ]
        for normalized_skill, entries
        in cached_index.items()
    }


def get_available_categories() -> list[str]:
    """
    Return all available skill categories.
    """

    knowledge_base = _load_cached_knowledge_base()

    return sorted(knowledge_base.keys())


def clear_knowledge_cache() -> None:
    """
    Clear the loader cache.

    Use this after editing JSON files while the same
    Python process is still running.
    """

    _load_cached_knowledge_base.cache_clear()
    _build_cached_skill_index.cache_clear()