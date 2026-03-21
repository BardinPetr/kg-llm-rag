from src.visual.analyze.detection.main import DiagramNodesDetector
from src.visual.analyze.ocr.reader_easyocr import OCRReaderEasyocr

app_det = DiagramNodesDetector.bind()
app_ocr = OCRReaderEasyocr.bind("ru")

