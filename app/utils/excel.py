from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def build_xlsx(sheet_name: str, headers: list[str], rows: list[list]) -> bytes:
    """Build a single-sheet .xlsx workbook from headers + rows."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]

    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        ws.append(row)

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
