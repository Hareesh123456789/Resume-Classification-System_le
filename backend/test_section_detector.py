from parser.pdf_parser import extract_text_from_pdf
from parser.section_detector import detect_sections

pdf_path = "../sample_resume/Resume.pdf"

text = extract_text_from_pdf(pdf_path)

sections = detect_sections(text)

print("=" * 80)

for heading, content in sections.items():

    print()

    print(f"[ {heading} ]")

    print("-" * 50)

    print(content[:500])