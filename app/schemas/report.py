from uuid import UUID

from pydantic import BaseModel


class StockReportItem(BaseModel):
    supplier_uuid: UUID
    supplier_name: str

    area_uuid: UUID
    area_name: str

    quantity: int


class TransactionReportItem(BaseModel):
    transaction_uuid: UUID

    type: str

    supplier_name: str
    area_name: str
    unit_name: str

    quantity: int

    created_at: str