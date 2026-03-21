from document.pdf.odl_processor import PDFProcessorODL
from src.document.docling.docling_processor import PDFProcessorDocling, PDFProcessorDoclingVLM
from src.document.processor import DocumentProcessor
from src.document.table.table import DocumentTableProcessor

app = DocumentProcessor.bind(
    PDFProcessorDocling.bind(),
    PDFProcessorDoclingVLM.bind(),
    PDFProcessorODL.bind(),
    DocumentTableProcessor.bind(PDFProcessorDocling.bind())
)
