import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import os

# Configure Tesseract path for Windows
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path: str, doc_name: str) -> dict:
    """
    Extract text from a PDF file page by page.
    If a page has no text, apply OCR using pytesseract.
    
    Returns:
        pages_text: dict {page_number: page_text}
    """
    pages_text = {}

    # Open PDF
    doc = fitz.open(pdf_path)

    for page_number in range(len(doc)):
        page = doc[page_number]

        # Try to extract text
        text = page.get_text().strip()

        # If text is empty → scanned page → use OCR
        if not text:
            # Convert page to image
            pix = page.get_pixmap(dpi=300)  # high quality
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            # OCR
            text = pytesseract.image_to_string(img, lang="eng")
            text = text.strip()

        pages_text[page_number + 1] = text  # 1-indexed page numbers

    doc.close()
    return pages_text
