"""
---------------------------------------------------------
Skills Extractor
---------------------------------------------------------
Extract technical skills from the Skills section.
---------------------------------------------------------
"""

import re


def _extract_items(pattern, text):
    """
    Extract comma-separated items after a heading.
    """
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return []

    value = match.group(1).strip()

    skills = [
        item.strip()
        for item in re.split(r",|;", value)
        if item.strip()
    ]

    return skills


def extract_skills(text):

    result = {

        "programming_languages": [],
        "frameworks": [],
        "databases": [],
        "web_technologies": [],
        "ai_ml": [],
        "tools": []

    }

    result["programming_languages"] = _extract_items(
        r"Programming.*?\n(.+)",
        text
    )

    result["frameworks"] = _extract_items(
        r"Frameworks?.*?\n(.+)",
        text
    )

    result["databases"] = _extract_items(
        r"Database[s]?.*?\n(.+)",
        text
    )

    result["web_technologies"] = _extract_items(
        r"Web Technologies.*?\n(.+)",
        text
    )

    result["ai_ml"] = _extract_items(
        r"Artificial Intelligence.*?\n(.+)",
        text
    )

    result["tools"] = _extract_items(
        r"IoT.*?\n(.+)",
        text
    )

    return result