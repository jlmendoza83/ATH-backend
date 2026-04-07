from dataclasses import dataclass


@dataclass
class OperativaResult:
    ticker: str
    entry: float
    stop: float
    capital: float
    risk_pct: float
    timeframe: str
    risk_amount: float
    dist_abs: float
    dist_pct: float
    shares: int
    invested: float
    exposure_pct: float
    fee: float
    target_1r: float
    target_2r: float
    target_3r: float
    portfolio_risk_current: float
    portfolio_risk_new: float
    portfolio_risk_total: float


def calcular_posicion(
    ticker, entry, stop, capital, risk_pct,
    timeframe="weekly", fee=1.0, portfolio_risk_current=0.0,
) -> OperativaResult:
    if entry <= 0 or stop <= 0 or capital <= 0:
        raise ValueError("entry, stop y capital deben ser > 0")
    if stop >= entry:
        raise ValueError("stop debe ser menor que entry")
    if not (0.1 <= risk_pct <= 10):
        raise ValueError("risk_pct debe estar entre 0.1 y 10")

    risk_amount = round(capital * risk_pct / 100, 2)
    dist_abs    = round(entry - stop, 4)
    dist_pct    = round(dist_abs / entry * 100, 2)
    shares      = int(risk_amount // dist_abs)
    invested    = round(shares * entry, 2)
    exposure    = round(invested / capital * 100, 2)

    return OperativaResult(
        ticker=ticker, entry=entry, stop=stop,
        capital=capital, risk_pct=risk_pct, timeframe=timeframe,
        risk_amount=risk_amount, dist_abs=dist_abs, dist_pct=dist_pct,
        shares=shares, invested=invested, exposure_pct=exposure, fee=fee,
        target_1r=round(entry + dist_abs,     2),
        target_2r=round(entry + dist_abs * 2, 2),
        target_3r=round(entry + dist_abs * 3, 2),
        portfolio_risk_current=portfolio_risk_current,
        portfolio_risk_new=risk_pct,
        portfolio_risk_total=round(portfolio_risk_current + risk_pct, 2),
    )
