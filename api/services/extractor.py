import fitz  # pymupdf
from docx import Document
from fastapi import UploadFile, HTTPException
import io


SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "application/json": "txt",
}


async def extract_text(file: UploadFile) -> str:
    """
    Read an uploaded file and return its plain text content.
    Supports PDF, DOCX, and plain text/JSON.
    """
    content_type = file.content_type or ""
    file_type = SUPPORTED_TYPES.get(content_type)

    if not file_type:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {content_type}. Accepted: PDF, DOCX, TXT, JSON."
        )

    raw_bytes = await file.read()

    if file_type == "pdf":
        return _extract_from_pdf(raw_bytes)
    elif file_type == "docx":
        return _extract_from_docx(raw_bytes)
    else:
        return _extract_from_text(raw_bytes)


def _extract_from_pdf(data: bytes) -> str:
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        pages = [page.get_text() for page in doc]
        text = "\n".join(pages).strip()
        if not text:
            raise HTTPException(status_code=422, detail="PDF appears to be empty or scanned (no extractable text).")
        return text
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {str(e)}")


def _extract_from_docx(data: bytes) -> str:
    try:
        doc = Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        if not text:
            raise HTTPException(status_code=422, detail="DOCX appears to be empty.")
        return text
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read DOCX: {str(e)}")


def _extract_from_text(data: bytes) -> str:
    try:
        text = data.decode("utf-8").strip()
        if not text:
            raise HTTPException(status_code=422, detail="File is empty.")
        return text
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="Could not decode text file. Ensure it is UTF-8 encoded.")