from parser.pdf_parser import extract_text_from_pdf
from extractor.personal_info import extract_personal_info


pdf_path = "../sample_resume/Resume.pdf"

text = extract_text_from_pdf(pdf_path)

info = extract_personal_info(text)

print("=" * 60)
print("PERSONAL INFORMATION")
print("=" * 60)

for key, value in info.items():
    print(f"{key:10}: {value}")