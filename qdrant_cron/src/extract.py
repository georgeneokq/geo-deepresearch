import os
import magic
import fitz
from docx import Document

import logging

logger = logging.getLogger(__name__)
logging.basicConfig()

def extract_text(file_path: str):
    """
    Detect file type by magic bytes
    """
    mime = magic.Magic(mime=True)
    with open(file_path, 'rb') as f:
        blob = f.read(2048)
        file_type = mime.from_buffer(blob)
    
    print(f"Detected: {file_type} for {os.path.basename(file_path)}")

    try:
        # PDF Parsing
        if file_type == 'application/pdf':
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    page_text = page.get_text("text")
                    assert isinstance(page_text, str)
                    text += page_text

            return text

        # DOCX Parsing
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = Document(file_path)
            # Joins all paragraphs with newlines
            return "\n".join([para.text for para in doc.paragraphs])

        # Plain Text / Fallback
        elif 'text/' in file_type or file_type == 'application/x-empty':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        else:
            return f"Unsupported file type: {file_type}"

    except Exception as e:
        return f"Error processing {file_path}: {str(e)}"
