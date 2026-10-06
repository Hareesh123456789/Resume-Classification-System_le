import pymupdf as fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF resume.
    """

    try:
        document = fitz.open(pdf_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None