import os
import tempfile
import google.generativeai as genai
from PyPDF2 import PdfReader
import sys
from .. import prompts, config


def extract_text_from_pdf_bytes(pdf_bytes):
    """
    Extracts text from PDF bytes.
    Returns extracted text string on success, None on failure.
    """
    if not pdf_bytes:
        print(f"[ERROR] No PDF bytes provided.")
        return None

    try:
        # create temp file w bytes
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf.flush()

            print(f"Reading PDF from temporary file: {temp_pdf.name}...")

            reader = PdfReader(temp_pdf.name)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            if not text.strip():
                print(f"Warning: No text extracted from temporary PDF.")
                return None

            print("PDF text extracted successfully.")
            return text

    except Exception as e:
        print(f"[ERROR] Error reading PDF from bytes: {e}")
        return None
