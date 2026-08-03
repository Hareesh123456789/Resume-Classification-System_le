"""
---------------------------------------------------------
Resume Service
---------------------------------------------------------
Purpose:
Coordinates the complete resume analysis pipeline.

Pipeline:

PDF/DOCX
    ↓
Parser
    ↓
Text Cleaner
    ↓
Section Detector
    ↓
Extractors
    ↓
ResumeSchema
---------------------------------------------------------
"""

from parser.pdf_parser import extract_text_from_pdf
from parser.section_detector import detect_sections

from extractor.personal_info import extract_personal_info
from extractor.skills_extractor import extract_skills
from extractor.education_extractor import extract_education
from extractor.experience_extractor import extract_experience
from extractor.projects_extractor import extract_projects
from extractor.certification_extractor import extract_certifications

from schemas.resume_schema import (
    ResumeSchema,
    PersonalInfo,
    Skills,
    Education,
    Experience,
    Project,
    Certification
)


class ResumeService:

    def analyze_resume(self, pdf_path: str):

        # ----------------------------------------
        # Step 1 : Read Resume
        # ----------------------------------------

        text = extract_text_from_pdf(pdf_path)

        if not text:
            raise ValueError("Unable to extract text from resume.")

        # ----------------------------------------
        # Step 2 : Detect Sections
        # ----------------------------------------

        sections = detect_sections(text)

        # ----------------------------------------
        # Step 3 : Extract Information
        # ----------------------------------------

        personal = extract_personal_info(
            sections.get("HEADER", "")
        )

        skills = extract_skills(
            sections.get("SKILLS", "")
        )

        education = extract_education(
            sections.get("EDUCATION", "")
        )

        experience = extract_experience(
            sections.get("EXPERIENCE", "")
        )

        projects = extract_projects(
            sections.get("PROJECT EXPERIENCE", "")
        )

        certifications = extract_certifications(
            sections.get("CERTIFICATIONS", "")
        )

        # ----------------------------------------
        # Step 4 : Build JSON Schema
        # ----------------------------------------

        resume = ResumeSchema(

            personal_info=PersonalInfo(**personal),

            skills=Skills(**skills),

            education=[
                Education(**item)
                for item in education
            ],

            experience=[
                Experience(**item)
                for item in experience
            ],

            projects=[
                Project(**item)
                for item in projects
            ],

            certifications=[
                Certification(**item)
                for item in certifications
            ]

        )

        return resume