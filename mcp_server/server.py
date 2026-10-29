"""
MCP Server for DocFlow Agent.
Exposes standard tools for file management and structured Excel report generation.
"""

from mcp.server.fastmcp import FastMCP
import pandas as pd
import os
from pathlib import Path

# Initialize the FastMCP server
mcp = FastMCP("DocFlow Excel Server")

# Define output path for the processed Excel file
EXCEL_PATH = Path("./output/processed_invoices.xlsx")


@mcp.tool()
def append_invoice_to_excel(
        provider: str,
        tax_id: str,
        date: str,
        subtotal: float,
        vat: float,
        total: float
) -> str:
    """
    Appends a row with structured invoice data to the local Excel file.
    Creates the file automatically if it does not exist.

    Args:
        provider: Name of the vendor or provider.
        tax_id: Tax ID or NIF of the provider.
        date: Invoice issue date (YYYY-MM-DD).
        subtotal: Tax-exclusive amount.
        vat: Value Added Tax amount.
        total: Total amount including tax.

    Returns:
        Confirmation message indicating success.
    """
    # Ensure the output directory exists
    EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    new_row = {
        "Provider": [provider],
        "Tax ID": [tax_id],
        "Date": [date],
        "Subtotal": [subtotal],
        "VAT": [vat],
        "Total": [total]
    }

    df_new = pd.DataFrame(new_row)

    # If the file already exists, append the new row; otherwise, create a new file
    if EXCEL_PATH.exists():
        df_existing = pd.read_excel(EXCEL_PATH)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_final = df_new

    df_final.to_excel(EXCEL_PATH, index=False)

    return f"Invoice from {provider} successfully appended to Excel at {EXCEL_PATH}."


if __name__ == "__main__":
    # Run the MCP server using standard transport (stdio)
    mcp.run()