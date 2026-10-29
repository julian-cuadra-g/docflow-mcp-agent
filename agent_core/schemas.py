"""
Pydantic schemas for structured invoice data extraction.
"""

from pydantic import BaseModel, Field

class InvoiceSchema(BaseModel):
    """Structured representation of an extracted invoice."""
    provider: str = Field(description="Name of the vendor or provider company.")
    tax_id: str = Field(description="Tax ID or NIF of the provider.")
    date: str = Field(description="Invoice issue date in YYYY-MM-DD format.")
    subtotal: float = Field(description="Tax-exclusive amount of the invoice.")
    vat: float = Field(description="Value Added Tax (VAT) amount.")
    total: float = Field(description="Total amount including tax.")
    