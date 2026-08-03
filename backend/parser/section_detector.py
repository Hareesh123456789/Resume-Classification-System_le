"""
---------------------------------------------------------
Resume Section Detector
---------------------------------------------------------
Purpose:
Split a resume into logical sections.
---------------------------------------------------------
"""

import re

SECTION_HEADINGS = [
    "CAREER OBJECTIVE",
    "OBJECTIVE",
    "PROFILE",
    "SUMMARY",
    "SKILLS",
    "TECHNICAL SKILLS",
    "EDUCATION",
    "ACADEMIC PROFILE",
    "PROJECTS",
    "PROJECT EXPERIENCE",
    "EXPERIENCE",
    "WORK EXPERIENCE",
    "INTERNSHIP",
    "CERTIFICATIONS",
    "ACHIEVEMENTS",
    "KEY ACHIEVEMENTS",
    "PERSONAL DETAILS",
    "DECLARATION"
]


def normalize_heading(line):
    """
    Normalize heading text.
    """
    line = re.sub(r'[^A-Za-z ]', '', line)
    line = line.strip().upper()
    return line


def detect_sections(text):

    sections = {}

    current_section = "HEADER"

    sections[current_section] = []

    lines = text.splitlines()

    for line in lines:

        clean = line.strip()

        if not clean:
            continue

        heading = normalize_heading(clean)

        if heading in SECTION_HEADINGS:

            current_section = heading

            if current_section not in sections:
                sections[current_section] = []

        else:

            sections[current_section].append(clean)

    for key in sections:
        sections[key] = "\n".join(sections[key])

    return sections