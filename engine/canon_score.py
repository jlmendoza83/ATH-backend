from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoreBreakdown:
    proximidad_ath:     int
    roic:               int
    crecimiento_ventas: int
    fortaleza_tecnica:  int
    margen_neto:        int
    solidez_balance:    int
    volumen_liquidez:   int
    total:              int


def calcular_canon_score(
    ath_pct=None, roic=None, sales_cagr_3y=None, perf_1y=None,
    net_margin=None, debt_equity=None, current_ratio=None,
    rel_volume=None, market_cap=None,
) -> ScoreBreakdown:

    p_ath = 0
    if ath_pct is not None:
        if ath_pct >= -2:    p_ath = 25
        elif ath_pct >= -5:  p_ath = 22
        elif ath_pct >= -10: p_ath = 18
        elif ath_pct >= -15: p_ath = 12
        elif ath_pct >= -20: p_ath = 7
        elif ath_pct >= -30: p_ath = 3

    p_roic = 0
    if roic is not None:
        if roic >= 50:    p_roic = 20
        elif roic >= 30:  p_roic = 17
        elif roic >= 20:  p_roic = 13
        elif roic >= 15:  p_roic = 9
        elif roic >= 8:   p_roic = 5

    p_ventas = 0
    if sales_cagr_3y is not None:
        if sales_cagr_3y >= 40:   p_ventas = 20
        elif sales_cagr_3y >= 25: p_ventas = 17
        elif sales_cagr_3y >= 15: p_ventas = 13
        elif sales_cagr_3y >= 8:  p_ventas = 8
        elif sales_cagr_3y >= 3:  p_ventas = 4

    p_tec = 0
    if perf_1y is not None:
        if perf_1y >= 100:   p_tec = 15
        elif perf_1y >= 50:  p_tec = 13
        elif perf_1y >= 25:  p_tec = 10
        elif perf_1y >= 10:  p_tec = 7
        elif perf_1y >= 0:   p_tec = 4
        elif perf_1y >= -15: p_tec = 2

    p_mg = 0
    if net_margin is not None:
        if net_margin >= 30:   p_mg = 10
        elif net_margin >= 20: p_mg = 8
        elif net_margin >= 12: p_mg = 6
        elif net_margin >= 5:  p_mg = 3

    p_bal = 0
    if debt_equity is not None:
        if debt_equity <= 0:    p_bal = 5
        elif debt_equity <= 0.3:p_bal = 4
        elif debt_equity <= 1:  p_bal = 3
        elif debt_equity <= 2:  p_bal = 1
    if current_ratio is not None and current_ratio >= 2:
        p_bal = min(5, p_bal + 1)

    p_vol = 0
    if rel_volume is not None:
        if rel_volume >= 2:    p_vol = 5
        elif rel_volume >= 1.5:p_vol = 4
        elif rel_volume >= 1:  p_vol = 3
        elif rel_volume >= 0.5:p_vol = 1
    if market_cap is not None and market_cap < 100_000_000:
        p_vol = max(0, p_vol - 2)

    total = p_ath + p_roic + p_ventas + p_tec + p_mg + p_bal + p_vol
    return ScoreBreakdown(p_ath, p_roic, p_ventas, p_tec, p_mg, p_bal, p_vol, total)
