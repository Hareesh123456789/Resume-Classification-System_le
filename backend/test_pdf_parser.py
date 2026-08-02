from parser.pdf_parser import extract_text_from_pdf

pdf_path = "../sample_resume/Resume.pdf"

text = extract_text_from_pdf(pdf_path)

print("=" * 80)
print("Extracted Resume Text")
print("=" * 80)
print(text)