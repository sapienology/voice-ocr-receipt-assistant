
from typing import List, Optional

from pydantic import BaseModel, Field


class ReceiptItem(BaseModel):
    name: str
    quantity: Optional[float] = 1
    price: Optional[float] = None


class Receipt(BaseModel):
    merchant: Optional[str] = None
    date: Optional[str] = None
    invoice_number: Optional[str] = None

    items: List[ReceiptItem] = Field(default_factory=list)

    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None

