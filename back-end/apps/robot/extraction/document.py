from dataclasses import asdict, dataclass
import hashlib
from io import BytesIO
import json
import re
from pathlib import Path


EXTRACTOR_VERSION = "mga-1.0"
MAX_BYTES = 15 * 1024 * 1024
MAX_PAGES = 40
MAX_PIXELS = 16_000_000


class ExtractionError(ValueError):
    pass


@dataclass
class ExtractedPage:
    number: int
    method: str
    text: str
    words: list
    tables: list
    width: float
    height: float


class DocumentExtractor:
    """Texto/tabelas nativos primeiro; OCR de imagens com coordenadas depois."""

    def __init__(self, cache_dir=None, progress=None):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.progress = progress or (lambda message: None)
        self.engine = None

    def ocr(self, image):
        if image.width * image.height > MAX_PIXELS:
            raise ExtractionError("Página excede o limite de pixels para OCR.")
        if self.engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self.engine = RapidOCR(det_model_path=None, det_limit_side_len=2400)
        import numpy as np

        results, _ = self.engine(np.array(image.convert("RGB")))
        words = []
        for box, text, score in results or []:
            words.append({"text": text, "x0": float(min(point[0] for point in box)), "x1": float(max(point[0] for point in box)),
                          "top": float(min(point[1] for point in box)), "bottom": float(max(point[1] for point in box)), "score": float(score)})
        words.sort(key=lambda word: (word["top"], word["x0"]))
        return words

    def extract(self, content, filename, allow_ocr=True):
        if not content or len(content) > MAX_BYTES:
            raise ExtractionError("Arquivo vazio ou maior que 15 MB.")
        digest = hashlib.sha256(content).hexdigest()
        cache = self.cache_dir / f"{digest}-{EXTRACTOR_VERSION}-ocr{int(allow_ocr)}.json" if self.cache_dir else None
        if cache and cache.exists():
            self.progress("Extração reutilizada pelo hash do conteúdo.")
            return [ExtractedPage(**page) for page in json.loads(cache.read_text(encoding="utf-8"))]
        pages = []
        if content.startswith(b"%PDF-"):
            import pdfplumber
            import pypdfium2

            try:
                with pdfplumber.open(BytesIO(content)) as pdf:
                    if len(pdf.pages) > MAX_PAGES:
                        raise ExtractionError("PDF excede 40 páginas.")
                    renderer = None
                    try:
                        for number, page in enumerate(pdf.pages, start=1):
                            self.progress(f"Página {number}/{len(pdf.pages)}: procurando caracteres e tabelas.")
                            text = page.extract_text() or ""
                            tables = page.extract_tables() if text.strip() else []
                            words = [{**{key: word[key] for key in ("text", "x0", "x1", "top", "bottom")}, "score": 1.0} for word in page.extract_words()]
                            # Camadas vazias ou quase vazias (inclusive PDFs híbridos)
                            # não impedem recuperar a tabela rasterizada.
                            native_table = any(sum(bool(cell) for cell in row) >= 4 for table in tables for row in table)
                            has_unit_header = "unidade" in text.casefold() and ("valor" in text.casefold() or "preço" in text.casefold())
                            has_values = len(re.findall(r"\d[\d .]*,\d{2}", text)) >= 2
                            damaged_text = "(cid:" in text or text.count("\ufffd") > max(3, len(text) // 100)
                            native_usable = (native_table or (len(words) >= 15 and has_unit_header)) and has_values and not damaged_text
                            if allow_ocr and not native_usable:
                                self.progress(f"Página {number}: camada insuficiente; executando OCR local.")
                                if renderer is None:
                                    renderer = pypdfium2.PdfDocument(content)
                                rendered = renderer[number - 1]
                                try:
                                    if rendered.get_width() * rendered.get_height() * 4 > MAX_PIXELS:
                                        raise ExtractionError("Página excede o limite de renderização.")
                                    bitmap = rendered.render(scale=2)
                                    try:
                                        image = bitmap.to_pil()
                                        words = self.ocr(image)
                                        pages.append(ExtractedPage(number, "ocr", "\n".join(word["text"] for word in words), words, [], image.width, image.height))
                                    finally:
                                        bitmap.close()
                                finally:
                                    rendered.close()
                            else:
                                pages.append(ExtractedPage(number, "texto", text, words, tables, page.width, page.height))
                    finally:
                        if renderer is not None:
                            renderer.close()
            except ExtractionError:
                raise
            except Exception as exc:
                raise ExtractionError(f"Não foi possível extrair o PDF ({type(exc).__name__}).") from None
        else:
            from PIL import Image, UnidentifiedImageError

            if not allow_ocr:
                raise ExtractionError("Imagem exige OCR; execução está configurada sem OCR.")
            try:
                with Image.open(BytesIO(content)) as image:
                    if image.width * image.height > MAX_PIXELS:
                        raise ExtractionError("Imagem excede limite de pixels.")
                    words = self.ocr(image)
                    pages.append(ExtractedPage(1, "ocr", "\n".join(word["text"] for word in words), words, [], image.width, image.height))
            except (UnidentifiedImageError, OSError):
                raise ExtractionError("Formato inválido. Envie PDF, PNG ou JPEG.") from None
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache.with_suffix(".tmp")
            temporary.write_text(json.dumps([asdict(page) for page in pages], ensure_ascii=False), encoding="utf-8")
            temporary.replace(cache)
        return pages
