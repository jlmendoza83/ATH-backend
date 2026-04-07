"""
FMP Provider — endpoints /stable/ para cuentas post-agosto 2025
"""
import time
import requests
from datetime import datetime
from .base import DataProvider, PriceData, FundamentalsData, SalesHistory, YearRevenue


class FMPProvider(DataProvider):
    BASE = "https://financialmodelingprep.com/stable"
    SLEEP = 0.25

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("FMP_API_KEY vacia")
        self._key = api_key
        self._s = requests.Session()

    def _get(self, path, params=None, retries=3):
        p = {"apikey": self._key}
        if params:
            p.update(params)
        url = f"{self.BASE}{path}"
        for attempt in range(retries):
            try:
                time.sleep(self.SLEEP)
                r = self._s.get(url, params=p, timeout=15)
                if r.status_code == 429:
                    time.sleep(60)
                    continue
                if r.status_code == 403:
                    raise ValueError(f"403 plan no cubre: {path}")
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and "Error Message" in data:
                    raise ValueError(data["Error Message"])
                return data
            except Exception as e:
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return []

    def get_price(self, ticker: str) -> PriceData:
        data = self._get("/quote", {"symbol": ticker})
        if not data:
            raise ValueError(f"Sin datos: {ticker}")
        q = data[0] if isinstance(data, list) else data

        price   = float(q.get("price") or 0)
        w52h    = float(q.get("yearHigh") or 0)
        volume  = int(q.get("volume") or 0)
        # FMP stable devuelve avgVolume — si es 0, usamos historical como fallback
        avg_vol = int(q.get("avgVolume") or q.get("averageVolume") or 0)

        # Si avg_volume es 0, intentar obtenerlo del historial de 20 días
        if avg_vol == 0:
            try:
                hist = self._get("/historical-price-eod/light",
                                 {"symbol": ticker, "limit": 20})
                if hist:
                    vols = [int(h.get("volume") or 0) for h in hist if h.get("volume")]
                    avg_vol = int(sum(vols) / len(vols)) if vols else 0
            except Exception:
                avg_vol = 0

        ath_pct = round((price - w52h) / w52h * 100, 2) if w52h > 0 else None
        rel_vol = round(volume / avg_vol, 2) if avg_vol > 0 else None

        return PriceData(
            ticker     = ticker,
            price      = price,
            change_pct = float(q.get("changesPercentage") or 0),
            w52_high   = w52h,
            w52_low    = float(q.get("yearLow") or 0),
            ath_pct    = ath_pct,
            volume     = volume,
            avg_volume = avg_vol,
            rel_volume = rel_vol,
            market_cap = float(q.get("marketCap") or 0) or None,
        )

    def get_fundamentals(self, ticker: str) -> FundamentalsData:
        km, km2, ra, pr = {}, {}, {}, {}
        try:
            r = self._get("/key-metrics", {"symbol": ticker, "limit": 2})
            if r:
                km = r[0]
                km2 = r[1] if len(r) > 1 else {}
        except Exception:
            pass
        try:
            r = self._get("/ratios", {"symbol": ticker, "limit": 1})
            if r:
                ra = r[0]
        except Exception:
            pass
        try:
            r = self._get("/profile", {"symbol": ticker})
            if isinstance(r, list) and r:
                pr = r[0]
            elif isinstance(r, dict):
                pr = r
        except Exception:
            pass

        def g(*keys):
            for k in keys:
                for d in [km, ra, pr]:
                    if d.get(k) is not None:
                        return d[k]
            return None

        def pct(v):
            if v is None:
                return None
            f = float(v)
            return round(f * 100, 2) if abs(f) <= 10 else round(f, 2)

        eps_g = None
        ec = km.get("eps") or km.get("netIncomePerShare")
        ep = km2.get("eps") or km2.get("netIncomePerShare")
        if ec and ep and float(ep) != 0:
            eps_g = round((float(ec) - float(ep)) / abs(float(ep)) * 100, 1)

        return FundamentalsData(
            ticker        = ticker,
            roic          = pct(g("roic", "returnOnInvestedCapital")),
            roe           = pct(g("returnOnEquity", "roe")),
            roa           = pct(g("returnOnAssets", "roa")),
            net_margin    = pct(g("netProfitMargin", "netIncomeRatio")),
            gross_margin  = pct(g("grossProfitMargin")),
            pe_ttm        = g("priceEarningsRatio", "peRatio"),
            fwd_pe        = g("forwardPE"),
            peg           = g("priceEarningsToGrowthRatio", "pegRatio"),
            ps            = g("priceToSalesRatio"),
            pb            = g("priceToBookRatio", "priceBookValueRatio"),
            debt_equity   = g("debtEquityRatio", "totalDebtToEquity"),
            current_ratio = g("currentRatio"),
            debt_ebitda   = g("netDebtToEBITDA", "debtToEbitda"),
            eps_ttm       = g("eps", "netIncomePerShare"),
            eps_growth_yoy= eps_g,
            insider_own   = pct(g("insidersOwnership")),
            target_price  = pr.get("dcf"),
            sector        = pr.get("sector"),
            industry      = pr.get("industry"),
        )

    def get_sales_history(self, ticker: str, years: int = 5) -> SalesHistory:
        try:
            # FMP stable: period=annual es obligatorio para estados anuales
            raw = self._get("/income-statement",
                            {"symbol": ticker, "period": "annual", "limit": years + 1})
        except Exception:
            return SalesHistory(ticker=ticker, years=[])
        if not raw:
            return SalesHistory(ticker=ticker, years=[])

        rows = list(reversed(raw[:years + 1]))
        year_data = []
        for i, row in enumerate(rows):
            rev = float(row.get("revenue") or 0) / 1e9
            period = str(row.get("calendarYear") or
                         str(row.get("date", ""))[:4] or "0")
            growth = None
            if i > 0 and year_data and year_data[-1].revenue > 0:
                growth = round((rev - year_data[-1].revenue) / year_data[-1].revenue * 100, 1)
            year_data.append(YearRevenue(
                year=int(period) if period.isdigit() else 0,
                revenue=round(rev, 2),
                growth_pct=growth,
            ))

        cagr_3y = cagr_5y = None
        if len(year_data) >= 4:
            s, e = year_data[-4].revenue, year_data[-1].revenue
            if s > 0:
                cagr_3y = round(((e / s) ** (1/3) - 1) * 100, 1)
        if len(year_data) >= 6:
            s, e = year_data[-6].revenue, year_data[-1].revenue
            if s > 0:
                cagr_5y = round(((e / s) ** (1/5) - 1) * 100, 1)

        return SalesHistory(
            ticker=ticker, years=year_data,
            cagr_3y=cagr_3y, cagr_5y=cagr_5y,
            latest_yoy=year_data[-1].growth_pct if year_data else None,
        )

    def get_screener_universe(self, filters: dict) -> list:
        params = {"isActivelyTrading": "true", "limit": filters.get("limit", 500)}
        for k, fk in {
            "market_cap_min": "marketCapMoreThan",
            "market_cap_max": "marketCapLowerThan",
            "sector": "sector", "exchange": "exchange", "country": "country",
        }.items():
            v = filters.get(k)
            if v and v not in ("all", ""):
                params[fk] = v
        raw = self._get("/company-screener", params)
        return [r.get("symbol") for r in raw if r.get("symbol")] if raw else []

    def get_bulk_metrics(self, tickers: list) -> list:
        results = []
        for ticker in tickers:
            try:
                results.append({
                    "ticker": ticker,
                    "price":  self.get_price(ticker),
                    "fund":   self.get_fundamentals(ticker),
                    "sales":  self.get_sales_history(ticker, years=4),
                    "sma":    {},
                })
            except Exception as e:
                print(f"[BATCH] ERR {ticker}: {e}")
        return results

    def health_check(self) -> dict:
        try:
            data = self._get("/quote", {"symbol": "AAPL"})
            return {"ok": bool(data), "provider": "FMPProvider", "endpoint": "stable"}
        except Exception as e:
            return {"ok": False, "error": str(e), "provider": "FMPProvider"}
