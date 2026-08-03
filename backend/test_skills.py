import json

from extractor.skills_extractor import (
    extract_skill_matches,
    extract_skills,
)
from parser.pdf_parser import extract_text_from_pdf
from parser.section_detector import detect_sections


def print_non_empty_categories(
    skills: dict[str, list[str]],
) -> None:

    for category, detected_skills in skills.items():

        if detected_skills:
            print(
                f"{category}: "
                f"{detected_skills}"
            )


def test_manual_sample() -> None:

    sample_text = """
    Programming
    Dsa with c++, python basics, java script

    Development
    HTML, CSS

    Database
    Oracle
    """

    print("=" * 75)
    print("MANUAL SKILLS TEST")
    print("=" * 75)

    skills = extract_skills(sample_text)

    print(
        json.dumps(
            skills,
            indent=4,
        )
    )

    print("\nNON-EMPTY CATEGORIES")
    print("-" * 75)

    print_non_empty_categories(skills)

    print("\nMATCH EVIDENCE")
    print("-" * 75)

    for match in extract_skill_matches(sample_text):
        print(match)


def test_resume_pdf() -> None:

    pdf_path = "../sample_resume/Resume.pdf"

    print("\n")
    print("=" * 75)
    print("RESUME PDF SKILLS TEST")
    print("=" * 75)

    text = extract_text_from_pdf(pdf_path)

    if not text:
        print("Unable to extract PDF text.")
        return

    sections = detect_sections(text)

    skills_text = sections.get("SKILLS", "")

    if not skills_text.strip():
        print(
            "SKILLS section was not detected. "
            "Using complete resume text."
        )
        skills_text = text

    skills = extract_skills(skills_text)

    print_non_empty_categories(skills)


if __name__ == "__main__":
    test_manual_sample()
    test_resume_pdf()