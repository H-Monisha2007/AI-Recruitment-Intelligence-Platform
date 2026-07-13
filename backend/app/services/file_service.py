"""
File validation and text extraction service.
"""
from __future__ import annotations
import io
import os
import pathlib
from typing import Tuple

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import FileTooLargeException, UnsupportedFileTypeException
from app.core.logging_config import get_logger

logger = get_logger(__name__)

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_file(filename: str, size: int) -> None:
    ext = pathlib.Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeException(
            f"File type '{ext}' is not allowed. Accepted: {settings.ALLOWED_EXTENSIONS}"
        )
    if size > MAX_BYTES:
        raise FileTooLargeException(
            f"File size {size / 1024 / 1024:.1f} MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB} MB"
        )


async def read_upload(file: UploadFile) -> Tuple[bytes, str]:
    """Read file contents, validate type and size, return (bytes, extension)."""
    content = await file.read()
    await file.seek(0)
    ext = pathlib.Path(file.filename or "").suffix.lower()
    validate_file(file.filename or "", len(content))
    return content, ext


async def extract_text(file: UploadFile) -> str:
    """Extract raw text from uploaded PDF / DOCX / TXT."""
    content, ext = await read_upload(file)
    return _extract_from_bytes(content, ext)


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    ext = pathlib.Path(filename).suffix.lower()
    return _extract_from_bytes(content, ext)


def _extract_from_bytes(content: bytes, ext: str) -> str:
    try:
        if ext == ".pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            return text.strip()
        elif ext == ".docx":
            from docx import Document
            doc = Document(io.BytesIO(content))
            return " ".join(p.text for p in doc.paragraphs if p.text.strip())
        elif ext == ".txt":
            for enc in ("utf-8", "latin-1", "cp1252"):
                try:
                    return content.decode(enc)
                except UnicodeDecodeError:
                    continue
            return content.decode("utf-8", errors="replace")
        else:
            raise UnsupportedFileTypeException(f"Cannot extract text from '{ext}' files")
    except (UnsupportedFileTypeException, FileTooLargeException):
        raise
    except Exception as exc:
        logger.error("Text extraction failed for ext=%s: %s", ext, exc)
        raise ValueError(f"Could not extract text from file: {exc}") from exc