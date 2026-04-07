from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class PriceData:
    ticker:     str
    price:      float
    change_pct: float
    w52_high:   float
    w52_low:    float
    ath_pct:    Optional[float] = None
    volume:     Optional[int]   = None
    avg_volume: Optional[int]   = None
    rel_volume: Optional[float] = None
    perf_1y:    Optional[float] = None
    market_cap: Optional[float] = None
    ath_absolute: Optional[float] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FundamentalsData:
    ticker:       str
    roic:         Optional[float] = None
    roe:          Optional[float] = None
    roa:          Optional[float] = None
    net_margin:   Optional[float] = None
    gross_margin: Optional[float] = None
    pe_ttm:       Optional[float] = None
    fwd_pe:       Optional[float] = None
    peg:          Optional[float] = None
    ps:           Optional[float] = None
    pb:           Optional[float] = None
    debt_equity:  Optional[float] = None
    current_ratio:Optional[float] = None
    debt_ebitda:  Optional[float] = None
    eps_ttm:      Optional[float] = None
    eps_growth_yoy:Optional[float]= None
    eps_next_y:   Optional[float] = None
    eps_next_5y:  Optional[float] = None
    insider_own:  Optional[float] = None
    short_float:  Optional[float] = None
    target_price: Optional[float] = None
    sector:       Optional[str]   = None
    industry:     Optional[str]   = None
    updated_at:   datetime = field(default_factory=datetime.utcnow)


@dataclass
class YearRevenue:
    year:       int
    revenue:    float
    growth_pct: Optional[float]
    is_estimate: bool = False


@dataclass
class SalesHistory:
    ticker:        str
    years:         list
    cagr_3y:       Optional[float] = None
    cagr_5y:       Optional[float] = None
    latest_yoy:    Optional[float] = None
    next_year_est: Optional[float] = None


class DataProvider(ABC):
    @abstractmethod
    def get_price(self, ticker: str) -> PriceData: pass
    @abstractmethod
    def get_fundamentals(self, ticker: str) -> FundamentalsData: pass
    @abstractmethod
    def get_sales_history(self, ticker: str, years: int = 5) -> SalesHistory: pass
    @abstractmethod
    def get_screener_universe(self, filters: dict) -> list: pass
    @abstractmethod
    def get_bulk_metrics(self, tickers: list) -> list: pass

    def get_ath_absolute(self, ticker: str) -> Optional[float]:
        try:
            import yfinance as yf
            hist = yf.Ticker(ticker).history(period="5y")
            if not hist.empty:
                return float(hist["High"].max())
        except Exception:
            pass
        return None

    def health_check(self) -> dict:
        try:
            self.get_price("AAPL")
            return {"ok": True, "provider": self.__class__.__name__}
        except Exception as e:
            return {"ok": False, "error": str(e)}
