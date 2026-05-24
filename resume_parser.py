import pdfminer.high_level
from docx import Document
import io
import re


def extract_text_from_pdf(file_bytes: bytes) -> str:
    return pdfminer.high_level.extract_text(io.BytesIO(file_bytes))


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def parse_resume(uploaded_file) -> str:
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Upload a PDF or DOCX.")


def extract_contact_info(text: str) -> dict:
    email = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', text)
    linkedin = re.findall(r'linkedin\.com/in/[\w\-]+', text)
    github = re.findall(r'github\.com/[\w\-]+', text)
    return {
        "email": email[0] if email else None,
        "phone": phone[0] if phone else None,
        "linkedin": linkedin[0] if linkedin else None,
        "github": github[0] if github else None,
    }