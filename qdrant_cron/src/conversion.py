from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

docling_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=PdfPipelineOptions()
        ),
    }
)

def convert_document_to_markdown(file_path: str | Path):
    converted = docling_converter.convert(file_path)
    
    # Export to markdown
    markdown_output = converted.document.export_to_markdown()

    return markdown_output
