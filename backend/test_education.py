from parser.pdf_parser import extract_text_from_pdf
from extractor.education_extractor import extract_education

pdf_path = "../sample_resume/Resume.pdf"

text = extract_text_from_pdf(pdf_path)

education = extract_education(text)

print("=" * 70)
print("EDUCATION DETAILS")
print("=" * 70)

for edu in education:

    print()

    print("Degree      :", edu["degree"])
    print("Branch      :", edu["branch"])
    print("College     :", edu["college"])
    print("University  :", edu["university"])
    print("Year        :", edu["year"])
    print("Score       :", edu["score"])