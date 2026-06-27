import re
import unicodedata
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies import require_permission
from app.models.user import User
from app.repositories.supplier_repo import SupplierRepository
from app.services.report_service import ReportService
from app.utils.excel import XLSX_MIME, build_xlsx

router = APIRouter(prefix="/reports", tags=["Reports"])


def _safe_label(name: str | None) -> str:
    """Filename-safe ASCII label for a supplier (or ALL when not filtered)."""
    if not name:
        return "ALL"
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^A-Za-z0-9]+", "_", ascii_name).strip("_")
    return ascii_name or "ALL"


def _filename(report_name: str, supplier_name: str | None) -> str:
    # Template: DD-MM-YYYY-<DOSTAWCA|ALL>-<report name>.xlsx
    today = date.today().strftime("%d-%m-%Y")
    return f"{today}-{_safe_label(supplier_name)}-{report_name}.xlsx"


async def _supplier_name(session, supplier_uuid: UUID | None) -> str | None:
    if not supplier_uuid:
        return None
    supplier = await SupplierRepository(session).get_one(uuid=supplier_uuid)
    return supplier.name if supplier else None


def _xlsx_response(sheet: str, headers: list[str], rows: list[list], filename: str) -> Response:
    content = build_xlsx(sheet, headers, rows)
    return Response(
        content=content,
        media_type=XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/ksiegowania")
async def booking_history(
    supplier_uuid: UUID | None = None,
    unit_uuid: UUID | None = None,
    area_uuid: UUID | None = None,
    start: date | None = None,
    end: date | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_permission("reports")),
):
    service = ReportService(session)
    sheet, headers, rows = await service.booking_history(
        supplier_uuid, unit_uuid, area_uuid, start, end
    )
    filename = _filename("Raport_ksiegowan", await _supplier_name(session, supplier_uuid))
    return _xlsx_response(sheet, headers, rows, filename)


@router.get("/saldo")
async def saldo(
    supplier_uuid: UUID | None = None,
    unit_uuid: UUID | None = None,
    area_uuid: UUID | None = None,
    start: date | None = None,
    end: date | None = None,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_permission("reports")),
):
    service = ReportService(session)
    sheet, headers, rows = await service.saldo(
        supplier_uuid, unit_uuid, area_uuid, start, end
    )
    report_name = "Saldo_zakres" if (start and end) else "Saldo"
    filename = _filename(report_name, await _supplier_name(session, supplier_uuid))
    return _xlsx_response(sheet, headers, rows, filename)
