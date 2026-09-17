
import json
import os
import re
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")

from PIL import Image

from app.models.receipt import Receipt, ReceiptItem


class ReceiptService:

    def __init__(self):

        self.model_name = os.getenv("RECEIPT_MODEL", "PP-OCRv5_mobile")
        self.model = None

        print("Receipt service created.")
        print("OCR model:", self.model_name)

    def load_model(self):

        """
        Load the Donut model only when we need it.
        Falls back gracefully if the external model cannot load.
        """

        if self.model is not None:
            return

        try:
            print("Loading PaddleOCR models...")
            from paddleocr import PaddleOCR

            self.model = PaddleOCR(
                lang="en",
                text_detection_model_name=os.getenv(
                    "RECEIPT_DETECTION_MODEL",
                    "PP-OCRv5_mobile_det"
                ),
                text_recognition_model_name=os.getenv(
                    "RECEIPT_RECOGNITION_MODEL",
                    "PP-OCRv5_mobile_rec"
                ),
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            print("PaddleOCR model loaded successfully!")

        except Exception as error:
            print("PaddleOCR model could not be loaded.")
            print(error)
            self.model = None
            raise

    def extract_receipt(self, image_path):

        """
        Extract information from a receipt image.
        If the OCR model is unavailable, return a safe fallback receipt.
        """
        try:
            self.load_model()
            result = self.model.predict(image_path)
            payload = result[0].json if result else {}
            raw = payload.get("res", payload) if isinstance(payload, dict) else {}
            texts = raw.get("rec_texts", [])
            scores = raw.get("rec_scores", [])
            lines = [
                text.strip()
                for index, text in enumerate(texts)
                if text and (not scores or scores[index] >= 0.35)
            ]
            return self.parse_text(lines, image_path)

        except Exception as error:
            print("Receipt OCR failed, using safe fallback values.")
            print(error)
            return self.create_fallback_receipt(image_path)

    def parse_text(self, lines, image_path):
        """Convert general OCR text into the stable receipt response schema."""
        text = "\n".join(lines)
        number = r"(?:[$€£₦]\s*)?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)"

        def find_amount(labels):
            pattern = rf"(?:{'|'.join(labels)})[^0-9]*{number}"
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            return self.convert_number(matches[-1]) if matches else None

        total = find_amount(["total", "amount due", "grand total"])
        tax = find_amount(["tax", "vat", "gst"])
        subtotal = find_amount(["subtotal", "sub total"])
        merchant = lines[0] if lines else "Uploaded receipt"
        items = []

        for line in lines[1:]:
            if re.search(r"(?:total|subtotal|tax|vat|cash|change|date|invoice)", line, re.IGNORECASE):
                continue
            if re.search(r"\d", line):
                items.append(ReceiptItem(name=line, quantity=1, price=None))

        return Receipt(
            merchant=merchant,
            items=items[:30],
            subtotal=subtotal,
            tax=tax,
            total=total,
        )

    def extract_document(self, file_path):
        """Process an image or return a valid result for an unsupported document."""
        suffix = Path(file_path).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            return self.extract_receipt(file_path)
        return self.create_fallback_receipt(file_path)

    def create_fallback_receipt(self, image_path):
        """Return a valid receipt object when OCR cannot run."""
        filename = os.path.basename(image_path)
        stem = os.path.splitext(filename)[0] or "receipt"

        try:
            with Image.open(image_path) as image:
                width, height = image.size
        except Exception:
            width = height = 0

        return Receipt(
            merchant="Uploaded receipt",
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            invoice_number=stem,
            items=[
                ReceiptItem(
                    name="Uploaded receipt image",
                    quantity=1,
                    price=0.0
                )
            ],
            subtotal=0.0,
            tax=0.0,
            total=0.0,
        )

    def parse_result(self, sequence):

        """
        Convert Donut's output into our Receipt object.
        """

        try:

            # Try to convert JSON-like output
            if self.processor is None:
                raise ValueError("OCR processor not available")

            data = self.processor.token2json(sequence)

            print("Parsed receipt:")
            print(data)

            return self.convert_to_receipt(data)

        except Exception as error:

            print("Could not parse Donut output.")
            print("Error:", error)

            return Receipt(
                merchant="Uploaded receipt",
                date=datetime.utcnow().strftime("%Y-%m-%d"),
                invoice_number="receipt",
                subtotal=0.0,
                tax=0.0,
                total=0.0,
                items=[ReceiptItem(name="Uploaded receipt image", quantity=1, price=0.0)]
            )

    def convert_to_receipt(self, data):

        """
        Convert Donut's dictionary into our Receipt model.
        """

        merchant = (
            data.get("merchant")
            or data.get("store")
            or data.get("supplier")
            or data.get("store_name")
        )

        date = data.get("date")

        invoice_number = (
            data.get("invoice_number")
            or data.get("invoice")
            or data.get("invoice_id")
        )

        subtotal_data = data.get("sub_total") or {}
        if not isinstance(subtotal_data, dict):
            subtotal_data = {}

        total_data = data.get("total") or {}
        if not isinstance(total_data, dict):
            total_data = {}

        subtotal = self.convert_number(
            data.get("subtotal") or subtotal_data.get("subtotal_price")
        )

        tax = self.convert_number(
            data.get("tax")
            or data.get("vat")
            or data.get("tax_price")
            or subtotal_data.get("tax_price")
        )

        total_value = data.get("total")
        if isinstance(total_value, dict):
            total_value = total_value.get("total_price") or total_value.get("total_etc")
        if isinstance(total_value, list):
            total_value = total_data.get("total_etc")
        total = self.convert_number(total_value or data.get("total_price"))

        items = []

        raw_items = data.get("items") or data.get("menu", [])

        if isinstance(raw_items, list):

            for item in raw_items:

                if isinstance(item, dict):

                    items.append(
                        ReceiptItem(
                            name=str(
                                    item.get("name") or item.get("nm", "Unknown")
                            ),
                            quantity=self.convert_number(
                                    item.get("quantity") or item.get("cnt")
                            ),
                            price=self.convert_number(
                                    item.get("price") or item.get("itemprice") or item.get("price")
                            )
                        )
                    )

        return Receipt(
            merchant=merchant,
            date=date,
            invoice_number=invoice_number,
            items=items,
            subtotal=subtotal,
            tax=tax,
            total=total
        )

    @staticmethod
    def convert_number(value):

        """
        Convert values such as:

        '₦10,500'
        '10,500.50'
        '10500'

        into Python numbers.
        """

        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        value = str(value)

        value = value.replace(",", "")
        value = value.replace("₦", "")
        value = value.replace("$", "")
        value = value.strip()

        try:
            return float(value)

        except ValueError:
            return None