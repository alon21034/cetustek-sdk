"""
Cetustek SDK Example

This example demonstrates how to use the Cetustek SDK to:
1. Create an e-invoice
2. Query an invoice
3. Cancel an invoice

Before running, replace the credentials with your actual Cetustek API credentials.
"""

from datetime import datetime

from cetustek import (
    Cetustek,
    CetustekAPIError,
    CreateInvoiceInput,
    CancelInvoiceInput,
    QueryInvoiceInput,
    InvoiceItem,
)


def main():
    # =========================================================================
    # Configuration - Replace with your actual credentials
    # =========================================================================
    client = Cetustek(
        endpoint="https://invoice.cetustek.com.tw/InvoiceMultiWeb/InvoiceAPI",
        rent_id="YOUR_RENT_ID",        # Your rent ID (統一編號)
        site_code="YOUR_SITE_CODE",    # Your site code
        api_password="YOUR_PASSWORD",  # Your API password
    )

    # =========================================================================
    # Example 1: Create an Invoice
    # =========================================================================
    print("=" * 60)
    print("Creating Invoice...")
    print("=" * 60)

    # Generate a unique order ID
    order_id = datetime.now().strftime("%Y%m%d%H%M%S")
    order_date = datetime.now().strftime("%Y/%m/%d")

    create_input = CreateInvoiceInput(
        order_id=order_id,
        order_date=order_date,
        # Buyer information (optional for B2C)
        buyer_identifier="12345678",       # Buyer's tax ID
        buyer_name="測試公司",
        buyer_email="test@example.com",
        # Invoice settings
        donate_mark="0",                   # 0: No donation
        invoice_type="07",                 # 07: B2B invoice
        tax_type="1",                      # 1: Taxable
        tax_rate=0.05,                     # 5% tax
        pay_way="1",                       # Payment method
        remark="SDK 測試發票",
        # Invoice items
        items=[
            InvoiceItem(
                production_code="PROD001",
                description="測試商品 A",
                quantity=2,
                unit_price=500,
                unit="件",
            ),
            InvoiceItem(
                production_code="PROD002",
                description="測試商品 B",
                quantity=1,
                unit_price=1000,
            ),
        ],
    )

    try:
        result = client.createInvoice(create_input)

        print(f"Invoice created successfully!")
        print(f"  Invoice Number: {result.invoice_number}")
        print(f"  Random Code: {result.random_code}")
        print(f"  Invoice Year: {result.invoice_year}")
    except CetustekAPIError as e:
        print(f"API Error: {e.code} - {e.message}")
        return
    except Exception as e:
        print(f"Failed to create invoice: {e}")
        return

    # =========================================================================
    # Example 2: Query the Invoice
    # =========================================================================
    print("\n" + "=" * 60)
    print("Querying Invoice...")
    print("=" * 60)

    query_input = QueryInvoiceInput(
        invoice_number=result.invoice_number,
        invoice_year=result.invoice_year,
    )

    try:
        query_result = client.queryInvoice(query_input)

        print(f"Invoice queried successfully!")
        print(f"  Invoice Number: {query_result.invoice_number}")
        print(f"  Order ID: {query_result.order_id}")
        print(f"  Random Code: {query_result.random_code}")
        print(f"  Buyer Name: {query_result.buyer_name}")
        print(f"  Seller Name: {query_result.seller_name}")
        print(f"  Total Amount: {query_result.total_amount}")
        print(f"  Invoice Status: {query_result.invoice_status}")
    except CetustekAPIError as e:
        print(f"API Error: {e.code} - {e.message}")
    except Exception as e:
        print(f"Failed to query invoice: {e}")

    # =========================================================================
    # Example 3: Cancel the Invoice
    # =========================================================================
    print("\n" + "=" * 60)
    print("Cancelling Invoice...")
    print("=" * 60)

    cancel_input = CancelInvoiceInput(
        invoice_number=result.invoice_number,
        invoice_year=result.invoice_year,
        remark="測試作廢",
    )

    try:
        # Use no_check=True to skip validation (for testing)
        cancel_result = client.cancelInvoice(cancel_input, no_check=True)

        if cancel_result.success:
            print(f"Invoice cancelled successfully!")
            print(f"  Code: {cancel_result.code}")
        else:
            print(f"Cancel failed with code: {cancel_result.code}")
    except Exception as e:
        print(f"Failed to cancel invoice: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
