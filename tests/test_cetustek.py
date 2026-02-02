"""
pytest tests for the Cetustek SDK.

Run:
  pip install -e ".[dev]"
  pytest -q
"""

from __future__ import annotations

import os
import random
import time
from datetime import datetime

import pytest

from cetustek import (
    Cetustek,
    CreateInvoiceInput,
    CreateInvoiceResponse,
    CancelInvoiceInput,
    CancelInvoiceResponse,
    QueryInvoiceInput,
    QueryInvoiceResponse,
    InvoiceItem,
)


@pytest.fixture()
def rent_id() -> str:
    rent_id = os.getenv("RENT_ID")
    assert rent_id is not None, "RENT_ID is not set"
    return rent_id


@pytest.fixture()
def site_code() -> str:
    site_code = os.getenv("SITE_CODE")
    assert site_code is not None, "SITE_CODE is not set"
    return site_code


@pytest.fixture()
def api_password() -> str:
    api_password = os.getenv("API_PASSWORD")
    assert api_password is not None, "API_PASSWORD is not set"
    return api_password


@pytest.fixture()
def sdk(rent_id: str, site_code: str, api_password: str) -> Cetustek:
    return Cetustek(
        endpoint="https://invoice.cetustek.com.tw/InvoiceMultiWeb/InvoiceAPI",
        rent_id=rent_id,
        site_code=site_code,
        api_password=api_password,
    )


@pytest.fixture()
def create_invoice_input() -> CreateInvoiceInput:
    # Generate random order ID
    order_id = str(random.randint(10000000, 99999999))

    # Get current date in yyyy/MM/dd format
    order_date = datetime.fromtimestamp(time.time()).strftime("%Y/%m/%d")

    return CreateInvoiceInput(
        order_id=order_id,
        order_date=order_date,
        buyer_identifier="53118823",
        buyer_name="鯨躍科技有限公司",
        buyer_email="test@cetustek.com.tw",
        donate_mark="0",
        invoice_type="07",
        tax_type="1",
        tax_rate=0.05,
        pay_way="1",
        remark="",
        items=[
            InvoiceItem(
                production_code="AA783456",
                description="DESCAA7890123456",
                quantity=1,
                unit="月",
                unit_price=50000,
            )
        ],
    )


@pytest.fixture()
def created_invoice(sdk: Cetustek, create_invoice_input: CreateInvoiceInput) -> CreateInvoiceResponse:
    """Create an invoice and return the response."""
    return sdk.createInvoice(create_invoice_input)


def test_create_invoice(sdk: Cetustek, create_invoice_input: CreateInvoiceInput):
    """Test createInvoice makes a real API call and returns success response."""
    result = sdk.createInvoice(create_invoice_input)

    # Verify response is a CreateInvoiceResponse
    assert isinstance(result, CreateInvoiceResponse)

    # Verify invoice number format
    assert len(result.invoice_number) == 10, "Invoice number should be 10 characters"
    assert result.invoice_number[0:2].isalpha(), "Invoice number should start with two letters"
    assert result.invoice_number[2:10].isdigit(), "Invoice number should end with 8 digits"

    # Verify random code format
    assert len(result.random_code) == 4, "Random code should be 4 characters"

    # Verify invoice_year property
    assert len(result.invoice_year) == 4, "Invoice year should be 4 digits"
    assert result.invoice_year.isdigit(), "Invoice year should be numeric"


def test_query_invoice(sdk: Cetustek, created_invoice: CreateInvoiceResponse):
    """Test queryInvoice makes a real API call and returns invoice details."""
    query_input = QueryInvoiceInput(
        invoice_number=created_invoice.invoice_number,
        invoice_year=created_invoice.invoice_year,
    )
    result = sdk.queryInvoice(query_input)

    # Verify response is a QueryInvoiceResponse
    assert isinstance(result, QueryInvoiceResponse)

    # Verify invoice number matches
    assert result.invoice_number == created_invoice.invoice_number

    # Verify key fields are present
    assert result.order_id is not None, "OrderID should be present"
    assert result.random_code is not None, "RandomNumber should be present"
    assert result.random_code == created_invoice.random_code, "Random code should match"

    # Verify raw_xml is available for additional parsing
    assert result.raw_xml is not None
    assert "<Invoice" in result.raw_xml or "<invoice" in result.raw_xml


def test_cancel_invoice(sdk: Cetustek, created_invoice: CreateInvoiceResponse):
    """Test cancelInvoice makes a real API call and returns success response."""
    cancel_input = CancelInvoiceInput(
        invoice_number=created_invoice.invoice_number,
        invoice_year=created_invoice.invoice_year,
        remark="測試作廢",
    )

    result = sdk.cancelInvoice(cancel_input, no_check=True)

    # Verify response is a CancelInvoiceResponse
    assert isinstance(result, CancelInvoiceResponse)

    # Verify success
    assert result.success is True, f"Cancel should succeed, got code: {result.code}"
    assert result.code == "C0", f"Success code should be 'C0', got: {result.code}"
