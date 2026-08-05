import io
from dataclasses import dataclass

import pikepdf
from pypdf import PdfReader, PdfWriter


@dataclass
class PdfValidationResult:
    is_valid: bool
    page_count: int
    is_encrypted: bool
    error: str | None = None


class PdfValidator:
    def validate(self, pdf_bytes: bytes) -> PdfValidationResult:
        if not pdf_bytes:
            return PdfValidationResult(
                is_valid=False,
                page_count=0,
                is_encrypted=False,
                error="Empty file.",
            )

        if not pdf_bytes.startswith(b"%PDF"):
            return PdfValidationResult(
                is_valid=False,
                page_count=0,
                is_encrypted=False,
                error="File does not appear to be a PDF.",
            )

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            is_encrypted = bool(reader.is_encrypted)

            if is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    pass

            return PdfValidationResult(
                is_valid=True,
                page_count=len(reader.pages),
                is_encrypted=is_encrypted,
            )

        except Exception as exc:
            return PdfValidationResult(
                is_valid=False,
                page_count=0,
                is_encrypted=False,
                error=str(exc),
            )


class PasswordRemover:
    def remove(self, pdf_bytes: bytes, password: str | None = None) -> bytes:
        try:
            pdf = pikepdf.open(io.BytesIO(pdf_bytes), password=password or "")
            output = io.BytesIO()
            pdf.save(output)
            return output.getvalue()
        except Exception:
            # If decryption fails, return original bytes and let downstream validation handle it.
            return pdf_bytes


class ImageEnhancer:
    def enhance(self, pdf_bytes: bytes) -> bytes:
        """
        Placeholder for image enhancement.

        Production implementation can use:
        - PyMuPDF to render pages
        - OpenCV for deskew/denoise
        - Pillow for image processing
        - Then reassemble enhanced PDF
        """
        return pdf_bytes


class PageSegmenter:
    def __init__(self, max_pages_per_batch: int = 25):
        self.max_pages_per_batch = max_pages_per_batch

    def split(self, pdf_bytes: bytes) -> list[bytes]:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = reader.pages

        if len(pages) <= self.max_pages_per_batch:
            return [pdf_bytes]

        parts: list[bytes] = []

        for start in range(0, len(pages), self.max_pages_per_batch):
            writer = PdfWriter()

            for page in pages[start : start + self.max_pages_per_batch]:
                writer.add_page(page)

            buffer = io.BytesIO()
            writer.write(buffer)
            parts.append(buffer.getvalue())

        return parts
