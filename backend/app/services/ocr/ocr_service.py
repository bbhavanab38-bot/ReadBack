from abc import ABC, abstractmethod
from typing import Dict, Any, List
from io import BytesIO
import os
import shutil

import fitz
from PIL import Image

from app.config import settings

class OCRResult:
    def __init__(self, raw_text: str, confidence: float, bounding_boxes: List[Dict[str, Any]], page_count: int = 1):
        self.raw_text = raw_text
        self.confidence = confidence
        self.bounding_boxes = bounding_boxes
        self.page_count = page_count

class BaseOCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> OCRResult:
        pass

    @abstractmethod
    def extract_image(self, image: Image.Image) -> OCRResult:
        pass

class SimulatedOCRProvider(BaseOCRProvider):
    """
    Direct text-file reader. It never simulates OCR for binary documents.
    """

    def extract_text(self, file_path: str) -> OCRResult:
        text_extensions = {".txt", ".text", ".csv", ".md"}
        extension = os.path.splitext(file_path)[1].lower()
        if extension in text_extensions and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as text_file:
                    content = text_file.read()
                return OCRResult(
                    raw_text=content,
                    confidence=0.96 if content.strip() else 0.0,
                    bounding_boxes=[],
                    page_count=1,
                )
            except (OSError, UnicodeDecodeError):
                pass

        return OCRResult(raw_text="", confidence=0.0, bounding_boxes=[], page_count=1)

    def extract_image(self, image: Image.Image) -> OCRResult:
        return OCRResult(raw_text="", confidence=0.0, bounding_boxes=[], page_count=1)

class PaddleOCRProvider(BaseOCRProvider):
    def __init__(self):
        self._ocr = None

    def extract_text(self, file_path: str) -> OCRResult:
        with Image.open(file_path) as image:
            return self.extract_image(image.convert("RGB"))

    def extract_image(self, image: Image.Image) -> OCRResult:
        from paddleocr import PaddleOCR
        import numpy as np

        if self._ocr is None:
            self._ocr = PaddleOCR(use_angle_cls=True, lang="en")
        result = self._ocr.ocr(np.array(image), cls=True)
        lines = result[0] if result and result[0] else []
        text_lines = []
        boxes = []
        confidences = []
        for line in lines:
            text, confidence = line[1]
            confidence = float(confidence)
            text_lines.append(text)
            confidences.append(confidence)
            boxes.append({"text": text, "box": line[0], "conf": confidence})
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return OCRResult("\n".join(text_lines), average_confidence, boxes)

class TesseractOCRProvider(BaseOCRProvider):
    def extract_text(self, file_path: str) -> OCRResult:
        with Image.open(file_path) as image:
            return self.extract_image(image.convert("RGB"))

    def extract_image(self, image: Image.Image) -> OCRResult:
        import pytesseract
        from pytesseract import Output

        command = settings.TESSERACT_CMD or os.getenv("TESSERACT_CMD") or shutil.which("tesseract")
        if command:
            pytesseract.pytesseract.tesseract_cmd = command
        elif os.path.isfile("/opt/homebrew/bin/tesseract"):
            pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

        data = pytesseract.image_to_data(image, output_type=Output.DICT)
        lines = {}
        boxes = []
        confidences = []
        for index, value in enumerate(data["text"]):
            word = value.strip()
            try:
                confidence = float(data["conf"][index]) / 100
            except (TypeError, ValueError):
                continue
            if word and confidence >= 0:
                line_key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
                lines.setdefault(line_key, []).append(word)
                confidences.append(confidence)
                boxes.append({
                    "text": word,
                    "box": [data["left"][index], data["top"][index], data["width"][index], data["height"][index]],
                    "conf": confidence,
                    "page": 1,
                })
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        text = "\n".join(" ".join(words) for words in lines.values())
        return OCRResult(text, average_confidence, boxes)


class OCRUnavailableError(RuntimeError):
    pass


class FallbackOCRProvider(BaseOCRProvider):
    def __init__(self, providers: List[BaseOCRProvider]):
        self.providers = providers

    def _extract(self, method: str, value: Any) -> OCRResult:
        errors = []
        for provider in self.providers:
            try:
                result = getattr(provider, method)(value)
            except Exception as error:
                errors.append(error)
                continue
            if result.raw_text.strip():
                return result
        if len(errors) == len(self.providers):
            raise OCRUnavailableError("All configured OCR engines failed.") from errors[-1]
        return OCRResult("", 0.0, [])

    def extract_text(self, file_path: str) -> OCRResult:
        return self._extract("extract_text", file_path)

    def extract_image(self, image: Image.Image) -> OCRResult:
        return self._extract("extract_image", image)


def extract_document_text(file_path: str, provider_name: str) -> OCRResult:
    extension = os.path.splitext(file_path)[1].lower()
    if extension in {".txt", ".text", ".csv", ".md"}:
        return SimulatedOCRProvider().extract_text(file_path)

    provider = get_ocr_provider(provider_name)
    if extension == ".pdf":
        page_texts = []
        bounding_boxes = []
        with fitz.open(file_path) as document:
            page_count = len(document)
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if len(text) < 10:
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
                        page_result = provider.extract_image(image.convert("RGB"))
                        text = page_result.raw_text.strip()
                        bounding_boxes.extend({**box, "page": page_number} for box in page_result.bounding_boxes)
                if text:
                    page_texts.append(text)
                    if not bounding_boxes or bounding_boxes[-1].get("page") != page_number:
                        bounding_boxes.append({"text": text, "page": page_number})
        return OCRResult("\n".join(page_texts), 0.90 if page_texts else 0.0, bounding_boxes, page_count)

    if extension in {".png", ".jpg", ".jpeg"}:
        with Image.open(file_path) as image:
            return provider.extract_image(image.convert("RGB"))

    raise ValueError("Unsupported document format.")

def get_ocr_provider(provider_name: str = "simulated") -> BaseOCRProvider:
    if provider_name.lower() == "paddleocr":
        return FallbackOCRProvider([PaddleOCRProvider(), TesseractOCRProvider()])
    elif provider_name.lower() == "tesseract":
        return TesseractOCRProvider()
    return SimulatedOCRProvider()
