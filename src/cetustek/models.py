from dataclasses import dataclass
from typing import Optional, List


# -------------------------
# Input Models
# -------------------------

@dataclass
class InvoiceItem:
    production_code: str      # ProductionCode
    description: str           # Description
    quantity: float            # Quantity
    unit_price: float          # UnitPrice
    unit: Optional[str] = None # Unit


@dataclass
class CreateInvoiceInput:
    order_id: str
    order_date: str                  # yyyy/MM/dd
    donate_mark: str                 # 0 / 1 / 2
    invoice_type: str                # 07 / 08
    pay_way: str                     # Table 4
    tax_type: str                    # 1 / 2 / 3 / 4 / 5 / 9

    items: List[InvoiceItem]

    # Optional buyer fields
    buyer_identifier: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_address: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_person_in_charge: Optional[str] = None
    buyer_tel: Optional[str] = None
    buyer_fax: Optional[str] = None
    buyer_customer_number: Optional[str] = None

    # Carrier / donation
    carrier_type: Optional[str] = None
    carrier_id1: Optional[str] = None
    carrier_id2: Optional[str] = None
    npoban: Optional[str] = None

    # Tax
    tax_rate: Optional[float] = 0.05
    remark: Optional[str] = None


@dataclass
class CancelInvoiceInput:
    invoice_number: str      # AA12345678
    invoice_year: str        # yyyy
    remark: str              # 作廢原因
    return_tax_document_number: Optional[str] = None


@dataclass
class QueryInvoiceInput:
    invoice_number: str
    invoice_year: str


# -------------------------
# Response Models
# -------------------------

@dataclass
class CreateInvoiceResponse:
    """Response from createInvoice API."""
    invoice_number: str  # 10-character invoice number (e.g., "WP20260002")
    random_code: str     # 4-digit random code (e.g., "6827")

    @property
    def invoice_year(self) -> str:
        """Extract year from invoice number (positions 2-5)."""
        return self.invoice_number[2:6]


@dataclass
class QueryInvoiceResponse:
    """Response from queryInvoice API."""
    invoice_number: str
    invoice_date: Optional[str] = None
    invoice_time: Optional[str] = None
    order_id: Optional[str] = None
    random_code: Optional[str] = None
    buyer_identifier: Optional[str] = None
    buyer_name: Optional[str] = None
    seller_identifier: Optional[str] = None
    seller_name: Optional[str] = None
    invoice_status: Optional[str] = None
    donate_mark: Optional[str] = None
    carrier_type: Optional[str] = None
    carrier_id: Optional[str] = None
    npoban: Optional[str] = None
    tax_type: Optional[str] = None
    sales_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    raw_xml: Optional[str] = None  # Original XML for additional parsing


@dataclass
class CancelInvoiceResponse:
    """Response from cancelInvoice API."""
    success: bool
    code: str  # "C0" for success, error code otherwise
    message: Optional[str] = None
