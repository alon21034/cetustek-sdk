import html
import re
from typing import Optional
from xml.sax.saxutils import escape

import requests

from cetustek.models import (
    CreateInvoiceInput,
    CreateInvoiceResponse,
    CancelInvoiceInput,
    CancelInvoiceResponse,
    QueryInvoiceInput,
    QueryInvoiceResponse,
)


class CetustekError(Exception):
    """Base exception for Cetustek API errors."""
    pass


class CetustekAPIError(CetustekError):
    """API returned an error response."""
    def __init__(self, code: str, message: Optional[str] = None):
        self.code = code
        self.message = message
        super().__init__(f"API Error: {code}" + (f" - {message}" if message else ""))


class Cetustek:
    def __init__(self, *, endpoint: str, rent_id: str, api_password: str, site_code: str):
        self.endpoint = endpoint
        self.rent_id = rent_id
        self.source = f"{site_code}{api_password}"

    # -------------------------
    # API methods
    # -------------------------

    def createInvoice(self, data: CreateInvoiceInput) -> CreateInvoiceResponse:
        """
        Create a new e-invoice.

        Returns:
            CreateInvoiceResponse with invoice_number and random_code.

        Raises:
            CetustekAPIError: If the API returns an error.
        """
        items_xml = ""
        for item in data.items:
            items_xml += f"""
<ProductItem>
  <ProductionCode>{escape(item.production_code)}</ProductionCode>
  <Description>{escape(item.description)}</Description>
  <Quantity>{item.quantity}</Quantity>
  {f"<Unit>{escape(item.unit)}</Unit>" if item.unit else ""}
  <UnitPrice>{item.unit_price}</UnitPrice>
</ProductItem>
"""

        invoice_xml = f"""
<Invoice XSDVersion="2.8">
<OrderId>{escape(data.order_id)}</OrderId>
<OrderDate>{data.order_date}</OrderDate>
<BuyerIdentifier>{data.buyer_identifier or ""}</BuyerIdentifier>
<BuyerName>{escape(data.buyer_name or "")}</BuyerName>
<BuyerAddress>{escape(data.buyer_address or "")}</BuyerAddress>
<BuyerEmailAddress>{escape(data.buyer_email or "")}</BuyerEmailAddress>
<DonateMark>{data.donate_mark}</DonateMark>
<InvoiceType>{data.invoice_type}</InvoiceType>
<CarrierType>{data.carrier_type or ""}</CarrierType>
<CarrierId1>{data.carrier_id1 or ""}</CarrierId1>
<CarrierId2>{data.carrier_id2 or ""}</CarrierId2>
<NPOBAN>{data.npoban or ""}</NPOBAN>
<PayWay>{data.pay_way}</PayWay>
<TaxType>{data.tax_type}</TaxType>
<TaxRate>{data.tax_rate}</TaxRate>
<Remark>{escape(data.remark or "")}</Remark>
<Details>
{items_xml}
</Details>
</Invoice>
"""

        inner = f"""
<invoicexml><![CDATA[{invoice_xml}]]></invoicexml>
<rentid>{self.rent_id}</rentid>
<source>{self.source}</source>
"""

        response_xml = self._post_soap(self._wrap_soap("CreateInvoiceV3", inner))
        return self._parse_create_response(response_xml)

    def cancelInvoice(self, data: CancelInvoiceInput, no_check: bool = False) -> CancelInvoiceResponse:
        """
        Cancel (void) an existing invoice.

        Args:
            data: CancelInvoiceInput with invoice details.
            no_check: If True, skip validation checks.

        Returns:
            CancelInvoiceResponse with success status and code.
        """
        invoice_xml = f"""
<Invoice XSDVersion="2.8">
<InvoiceNumber>{data.invoice_number}</InvoiceNumber>
<InvoiceYear>{data.invoice_year}</InvoiceYear>
<ReturnTaxDocumentNumber>{data.return_tax_document_number or ""}</ReturnTaxDocumentNumber>
<Remark>{escape(data.remark)}</Remark>
</Invoice>
"""

        inner = f"""
<invoicexml><![CDATA[{invoice_xml}]]></invoicexml>
<rentid>{self.rent_id}</rentid>
<source>{self.source}</source>
"""

        action = "CancelInvoiceNoCheck" if no_check else "CancelInvoice"
        response_xml = self._post_soap(self._wrap_soap(action, inner))
        return self._parse_cancel_response(response_xml)

    def queryInvoice(self, data: QueryInvoiceInput) -> QueryInvoiceResponse:
        """
        Query invoice by invoice number and year.

        Returns:
            QueryInvoiceResponse with invoice details.

        Raises:
            CetustekAPIError: If the API returns an error.
        """
        inner = f"""
<invoicenumber>{data.invoice_number}</invoicenumber>
<invoiceyear>{data.invoice_year}</invoiceyear>
<rentid>{self.rent_id}</rentid>
<source>{self.source}</source>
"""
        response_xml = self._post_soap(self._wrap_soap("QueryInvoice", inner))
        return self._parse_query_response(response_xml, data.invoice_number)

    # -------------------------
    # Response parsers
    # -------------------------

    def _parse_create_response(self, response_xml: str) -> CreateInvoiceResponse:
        """Parse createInvoice response XML."""
        return_value = self._extract_return_value(response_xml)

        if ";" not in return_value:
            raise CetustekAPIError(return_value)

        parts = return_value.split(";")
        if len(parts) != 2:
            raise CetustekAPIError(return_value, "Unexpected response format")

        invoice_number, random_code = parts
        return CreateInvoiceResponse(
            invoice_number=invoice_number,
            random_code=random_code,
        )

    def _parse_cancel_response(self, response_xml: str) -> CancelInvoiceResponse:
        """Parse cancelInvoice response XML."""
        return_value = self._extract_return_value(response_xml)

        success = return_value == "C0"
        return CancelInvoiceResponse(
            success=success,
            code=return_value,
            message=None if success else return_value,
        )

    def _parse_query_response(self, response_xml: str, invoice_number: str) -> QueryInvoiceResponse:
        """Parse queryInvoice response XML."""
        return_value = self._extract_return_value(response_xml, dotall=True)

        # Unescape HTML entities
        invoice_xml = html.unescape(return_value)

        # Check if response is an error (not XML)
        if not invoice_xml.strip().startswith("<"):
            raise CetustekAPIError(invoice_xml)

        # Parse invoice fields from XML
        return QueryInvoiceResponse(
            invoice_number=invoice_number,
            invoice_date=self._extract_xml_value(invoice_xml, "InvoiceDate"),
            invoice_time=self._extract_xml_value(invoice_xml, "InvoiceTime"),
            order_id=self._extract_xml_value(invoice_xml, "OrderID"),
            random_code=self._extract_xml_value(invoice_xml, "RandomNumber"),
            buyer_identifier=self._extract_xml_value(invoice_xml, "BuyerIdentifier"),
            buyer_name=self._extract_xml_value(invoice_xml, "BuyerName"),
            seller_identifier=self._extract_xml_value(invoice_xml, "SellerIdentifier"),
            seller_name=self._extract_xml_value(invoice_xml, "SellerName"),
            invoice_status=self._extract_xml_value(invoice_xml, "InvoiceStatus"),
            donate_mark=self._extract_xml_value(invoice_xml, "DonateMark"),
            carrier_type=self._extract_xml_value(invoice_xml, "CarrierType"),
            carrier_id=self._extract_xml_value(invoice_xml, "CarrierId1"),
            npoban=self._extract_xml_value(invoice_xml, "NPOBAN"),
            tax_type=self._extract_xml_value(invoice_xml, "TaxType"),
            sales_amount=self._extract_xml_float(invoice_xml, "SalesAmount"),
            tax_amount=self._extract_xml_float(invoice_xml, "TaxAmount"),
            total_amount=self._extract_xml_float(invoice_xml, "TotalAmount"),
            raw_xml=invoice_xml,
        )

    def _extract_return_value(self, response_xml: str, dotall: bool = False) -> str:
        """Extract the <return> value from SOAP response."""
        flags = re.DOTALL if dotall else 0
        match = re.search(r"<return>(.*?)</return>", response_xml, flags)
        if not match:
            raise CetustekError(f"Invalid response: missing <return> tag")
        return match.group(1).strip()

    def _extract_xml_value(self, xml: str, tag: str) -> Optional[str]:
        """Extract value from XML tag (case-insensitive)."""
        pattern = rf"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, xml, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            return value if value else None
        return None

    def _extract_xml_float(self, xml: str, tag: str) -> Optional[float]:
        """Extract float value from XML tag."""
        value = self._extract_xml_value(xml, tag)
        if value:
            try:
                return float(value)
            except ValueError:
                return None
        return None

    # -------------------------
    # Internal helpers
    # -------------------------

    def _post_soap(self, body: str) -> str:
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "Accept": "text/xml",
            "User-Agent": "Cetustek-Python-SDK/1.0",
        }
        resp = requests.post(self.endpoint, data=body.encode("utf-8"), headers=headers)
        resp.raise_for_status()
        return resp.text

    def _wrap_soap(self, action: str, inner_xml: str) -> str:
        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://webservice.cetustek.com/">
  <soap:Body>
    <tns:{action}>
      {inner_xml}
    </tns:{action}>
  </soap:Body>
</soap:Envelope>
"""
