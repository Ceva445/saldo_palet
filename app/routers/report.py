from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies import require_permission
from app.models.user import User
from app.services.report_service import ReportService
from app.utils.excel import XLSX_MIME, build_xlsx

router = APIRouter(prefix="/reports", tags=["Reports"])


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
    return _xlsx_response(sheet, headers, rows, "Stock_raport_ksiegowan.xlsx")


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
    filename = "Stock_saldo_zakres.xlsx" if (start and end) else "Stock_saldo.xlsx"
    return _xlsx_response(sheet, headers, rows, filename)
