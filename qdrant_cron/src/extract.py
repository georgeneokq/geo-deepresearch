import os
import httpx
from pathlib import Path
from util.logger import get_logger
import magic

logger = get_logger()


class DocumentProcessor:
    def __init__(self):
        # Do this once and reuse the instance.
        self.docling_base_url = os.environ.get(
            "DOCLING_BASE_URL", "http://docling-serve:5001"
        )

    async def extract_markdown(self, file_path: str | Path) -> str:
        """Assumes pdf documents"""
        url = f"{self.docling_base_url}/v1/convert/file"

        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(str(file_path))
        
        # Handle huge docs, wait up to 15 minutes
        timeout = httpx.Timeout(5.0, read=900.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            with open(file_path, "rb") as f:
                # Send file and options
                files = {"files": (os.path.basename(file_path), f, detected_mime)}
                data = {
                    "to_formats": ["md"],
                    "do_ocr": "true",
                    "pdf_backend": "dlparse_v2",
                    "table_mode": "fast",
                }
                response = await client.post(url, files=files, data=data)

                result = response.json()
                return result["document"]["md_content"]


document_processor = DocumentProcessor()

if __name__ == "__main__":
    # Test
    import asyncio
    from util.timeit import timeit
    from embedding import chunk_document
    @timeit
    async def test():
        file_path = "/app/ingest_docs/APT42s recent activity.pdf"
        contents = await document_processor.extract_markdown(file_path)
        print(chunk_document(contents))
    asyncio.run(test())