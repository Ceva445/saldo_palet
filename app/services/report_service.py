from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class ReportService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def stock_report(self):
        query = text("""
            SELECT
                s.name as supplier_name,
                a.name as area_name,
                p.quantity
            FROM pallets p
            JOIN suppliers s ON s.uuid = p.supplier_uuid
            JOIN areas a ON a.uuid = p.area_uuid
        """)

        result = await self.session.execute(query)
        return result.mappings().all()

    async def transaction_report(self):
        query = text("""
            SELECT
                t.uuid as transaction_uuid,
                t.type,
                s.name as supplier_name,
                a.name as area_name,
                u.name as unit_name,
                t.quantity,
                t.created_at
            FROM transactions t
            JOIN suppliers s ON s.uuid = t.supplier_uuid
            JOIN areas a ON a.uuid = t.area_uuid
            JOIN units u ON u.uuid = t.unit_uuid
        """)

        result = await self.session.execute(query)
        return result.mappings().all()