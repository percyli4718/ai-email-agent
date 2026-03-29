from pydantic import BaseModel, Field
from typing import List, Optional


class QuoteItemSchema(BaseModel):
    """Schema for a quote line item."""
    product_name: str
    product_code: Optional[str] = None
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    currency: str = "USD"
    incoterm: str
    lead_time_days: int = Field(gt=0)


class QuoteSchema(BaseModel):
    """Schema for generated quote."""
    quote_id: str
    customer_email: str
    items: List[QuoteItemSchema]
    total_amount: float = Field(gt=0)
    valid_until: str
    shipping_port: str
    payment_terms: str = "30% advance, 70% against B/L"
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": "QT-2026-0001",
                "customer_email": "customer@example.com",
                "items": [{
                    "product_name": "Paracetamol 500mg",
                    "product_code": "PAR-500",
                    "quantity": 50000,
                    "unit_price": 2.50,
                    "currency": "USD",
                    "incoterm": "FOB",
                    "lead_time_days": 30
                }],
                "total_amount": 125000.0,
                "valid_until": "2026-04-29",
                "shipping_port": "Shanghai",
                "payment_terms": "30% advance, 70% against B/L",
                "notes": "Subject to ANVISA approval"
            }
        }
