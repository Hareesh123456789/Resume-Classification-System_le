from parser.pdf_parser import extract_text_from_pdf
from parser.section_detector import detect_sections

from extractor.skills_extractor import extract_skills

text = extract_text_from_pdf("../sample_resume/Resume.pdf")

sections = detect_sections(text)

skills = extract_skills(
    sections.get("SKILLS", "")
)

print(skills)