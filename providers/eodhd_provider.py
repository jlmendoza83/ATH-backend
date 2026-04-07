from .base import DataProvider, PriceData, FundamentalsData, SalesHistory

class EODHDProvider(DataProvider):
    def __init__(self, api_key: str):
        self._key = api_key
    def get_price(self, t): raise NotImplementedError("EODHD no implementado en V1")
    def get_fundamentals(self, t): raise NotImplementedError
    def get_sales_history(self, t, years=5): raise NotImplementedError
    def get_screener_universe(self, f): raise NotImplementedError
    def get_bulk_metrics(self, t): raise NotImplementedError
