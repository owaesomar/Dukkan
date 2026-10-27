from datetime import datetime

from pydantic import BaseModel


class StoreAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    orders_count: int
    open_orders_count: int
    delivered_orders_count: int
    units_sold: int
    paid_revenue_by_currency: dict[str, int]
    new_customers_count: int
    published_products_count: int
    low_stock_variants_count: int
