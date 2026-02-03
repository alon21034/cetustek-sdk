# Cetustek

[![PyPI version](https://badge.fury.io/py/cetustek.svg)](https://badge.fury.io/py/cetustek)
[![Python](https://img.shields.io/pypi/pyversions/cetustek.svg)](https://pypi.org/project/cetustek/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python SDK for the [Cetustek](https://www.cetustek.com.tw/) Taiwan e-invoice API.

## Features

- Create, query, and cancel e-invoices
- Type-safe with dataclass request/response models
- Comprehensive error handling with custom exceptions
- Full support for B2B and B2C invoices

## Installation

```bash
pip install cetustek
```

**Requirements:** Python 3.9+

## Quick Start

```python
from cetustek import Cetustek, CreateInvoiceInput, InvoiceItem

client = Cetustek(
    endpoint="https://invoice.cetustek.com.tw/InvoiceMultiWeb/InvoiceAPI",
    rent_id="YOUR_RENT_ID",
    site_code="YOUR_SITE_CODE",
    api_password="YOUR_API_PASSWORD",
)

result = client.createInvoice(CreateInvoiceInput(
    order_id="12345678",
    order_date="2026/01/15",
    donate_mark="0",
    invoice_type="07",
    tax_type="1",
    pay_way="1",
    items=[InvoiceItem(
        production_code="PROD001",
        description="Product",
        quantity=1,
        unit_price=1000,
    )],
))

print(result.invoice_number)  # "WP20260002"
print(result.random_code)     # "6827"
```

## Usage

### Create Invoice

```python
from cetustek import CreateInvoiceInput, InvoiceItem, CetustekAPIError

try:
    result = client.createInvoice(CreateInvoiceInput(
        order_id="12345678",
        order_date="2026/01/15",
        donate_mark="0",              # 0: 載具, 1 捐贈, 2:紙本
        invoice_type="07",            # 07:一般稅額電子發票, 08:特種稅額電子發票
        tax_type="1",                 # 1:應稅, 2:零稅率(非經海關出口使用), 3:免稅, 4:應稅(特種稅率), 5:零稅率(經海關出口使用), 9:混合(應稅、零稅率與免稅)
        pay_way="1",
        items=[InvoiceItem(
            production_code="PROD001",
            description="Product description",
            quantity=1,
            unit_price=1000,
            unit="件",                # Optional
        )],
        # Optional buyer info
        buyer_identifier="12345678",  # Tax ID (統一編號)
        buyer_name="Company Name",
        buyer_email="email@example.com",
        tax_rate=0.05,                # Default: 5%
    ))

    print(result.invoice_number)      # "WP20260002"
    print(result.random_code)         # "6827"
    print(result.invoice_year)        # "2026" (derived property)

except CetustekAPIError as e:
    print(f"Error: {e.code}")
```

### Query Invoice

```python
from cetustek import QueryInvoiceInput

result = client.queryInvoice(QueryInvoiceInput(
    invoice_number="WP20260002",
    invoice_year="2026",
))

print(result.order_id)
print(result.buyer_name)
print(result.total_amount)
print(result.invoice_status)
```

### Cancel Invoice

```python
from cetustek import CancelInvoiceInput

result = client.cancelInvoice(CancelInvoiceInput(
    invoice_number="WP20260002",
    invoice_year="2026",
    remark="Cancellation reason",
))

if result.success:
    print("Invoice cancelled")
else:
    print(f"Failed: {result.code}")
```

## API Reference

### Client

| Parameter | Description |
|-----------|-------------|
| `endpoint` | Cetustek API endpoint URL |
| `rent_id` | Rent ID (統一編號) |
| `site_code` | Site code |
| `api_password` | API password |

### Response Models

**CreateInvoiceResponse**

| Field | Type | Description |
|-------|------|-------------|
| `invoice_number` | str | Invoice number (e.g., "WP20260002") |
| `random_code` | str | 4-digit random code |
| `invoice_year` | str | Year (derived from invoice_number) |

**QueryInvoiceResponse**

| Field | Type | Description |
|-------|------|-------------|
| `invoice_number` | str | Invoice number |
| `order_id` | str | Order ID |
| `random_code` | str | Random code |
| `buyer_identifier` | str | Buyer tax ID |
| `buyer_name` | str | Buyer name |
| `seller_identifier` | str | Seller tax ID |
| `seller_name` | str | Seller name |
| `invoice_status` | str | Status |
| `sales_amount` | float | Sales amount |
| `tax_amount` | float | Tax amount |
| `total_amount` | float | Total amount |
| `raw_xml` | str | Raw XML response |

**CancelInvoiceResponse**

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether cancellation succeeded |
| `code` | str | Response code ("C0" = success) |
| `message` | str | Error message (if failed) |

### Input Models

**InvoiceItem**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `production_code` | str | Yes | Product code |
| `description` | str | Yes | Description |
| `quantity` | float | Yes | Quantity |
| `unit_price` | float | Yes | Unit price |
| `unit` | str | No | Unit (e.g., "件") |

**CreateInvoiceInput**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `order_id` | str | Yes | Order ID |
| `order_date` | str | Yes | Date (yyyy/MM/dd) |
| `donate_mark` | str | Yes | 0/1/2 |
| `invoice_type` | str | Yes | 07 (B2B) / 08 (B2C) |
| `pay_way` | str | Yes | Payment method |
| `tax_type` | str | Yes | 1/2/3/4/5/9 |
| `items` | List | Yes | Invoice items |
| `buyer_identifier` | str | No | Buyer tax ID |
| `buyer_name` | str | No | Buyer name |
| `buyer_email` | str | No | Buyer email |
| `tax_rate` | float | No | Tax rate (default: 0.05) |
| `carrier_type` | str | No | Carrier type |
| `carrier_id1` | str | No | Carrier ID |
| `npoban` | str | No | NPO code |

## Error Handling

```python
from cetustek import CetustekError, CetustekAPIError

try:
    result = client.createInvoice(invoice_input)
except CetustekAPIError as e:
    print(f"API Error: {e.code} - {e.message}")
except CetustekError as e:
    print(f"SDK Error: {e}")
```

## Example

See [example.py](example.py) for a complete working example.

## Getting Started

```bash
pip install cetustek
```

```python
from cetustek import Cetustek, CreateInvoiceInput, InvoiceItem

# Initialize client
client = Cetustek(
    endpoint="https://invoice.cetustek.com.tw/InvoiceMultiWeb/InvoiceAPI",
    rent_id="YOUR_RENT_ID",
    site_code="YOUR_SITE_CODE",
    api_password="YOUR_API_PASSWORD",
)

# Create an invoice
result = client.createInvoice(CreateInvoiceInput(
    order_id="12345678",
    order_date="2026/01/15",
    donate_mark="0",
    invoice_type="07",
    tax_type="1",
    pay_way="1",
    items=[InvoiceItem(
        production_code="PROD001",
        description="Product",
        quantity=1,
        unit_price=1000,
    )],
))

print(result.invoice_number)  # e.g., "WP20260002"
print(result.random_code)     # e.g., "6827"
```

## License

MIT
