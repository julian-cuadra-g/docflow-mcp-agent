from mcp.server.fastmcp import FastMCP
import pandas as pd
from pathlib import Path

mcp = FastMCP("DocFlow Excel Server")
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
    """Appends a row with structured invoice data to the local Excel file."""
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

    if EXCEL_PATH.exists():
        df_existing = pd.read_excel(EXCEL_PATH)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_final = df_new

    df_final.to_excel(EXCEL_PATH, index=False)
    return f"Invoice from {provider} successfully appended to Excel at {EXCEL_PATH}."


if __name__ == "__main__":
    mcp.run()

