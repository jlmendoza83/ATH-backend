import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from config import DATA_PROVIDER, TICKER_UNIVERSE_V1
from cache.db import init_db, upsert_score, log_batch
from engine.canon_score import calcular_canon_score


def run():
    init_db()
    started = datetime.utcnow()
    print(f"[BATCH] {started.isoformat()}Z — {len(TICKER_UNIVERSE_V1)} tickers")
    ok, err, errors = 0, 0, []

    for item in DATA_PROVIDER.get_bulk_metrics(TICKER_UNIVERSE_V1):
        ticker = item["ticker"]
        try:
            p = item["price"]
            f = item["fund"]
            s = item["sales"]

            score = calcular_canon_score(
                ath_pct=p.ath_pct, roic=f.roic, sales_cagr_3y=s.cagr_3y,
                perf_1y=p.perf_1y, net_margin=f.net_margin,
                debt_equity=f.debt_equity, current_ratio=f.current_ratio,
                rel_volume=p.rel_volume, market_cap=p.market_cap,
            )
            upsert_score({
                "ticker": ticker, "name": f.sector or ticker,
                "canon_score": score.total,
                "price": p.price, "change_pct": p.change_pct,
                "w52_high": p.w52_high, "ath_pct": p.ath_pct,
                "rel_volume": p.rel_volume, "market_cap": p.market_cap,
                "roic": f.roic, "roe": f.roe, "roa": f.roa,
                "net_margin": f.net_margin, "gross_margin": f.gross_margin,
                "pe_ttm": f.pe_ttm, "fwd_pe": f.fwd_pe, "peg": f.peg,
                "ps": f.ps, "pb": f.pb, "debt_equity": f.debt_equity,
                "current_ratio": f.current_ratio, "debt_ebitda": f.debt_ebitda,
                "eps_ttm": f.eps_ttm, "eps_growth_yoy": f.eps_growth_yoy,
                "insider_own": f.insider_own, "target_price": f.target_price,
                "sector": f.sector, "sales_cagr_3y": s.cagr_3y,
                "sales_cagr_5y": s.cagr_5y, "sales_latest_yoy": s.latest_yoy,
                "batch_run_at": started.isoformat(), "error": None,
            })
            ok += 1
            print(f"[BATCH] OK  {ticker:<6} score={score.total}")
        except Exception as e:
            err += 1
            errors.append({"ticker": ticker, "error": str(e)})
            print(f"[BATCH] ERR {ticker:<6} {e}")
            upsert_score({"ticker": ticker, "error": str(e),
                          "batch_run_at": started.isoformat()})

    finished = datetime.utcnow()
    log_batch(started, finished, ok, err, errors)
    print(f"[BATCH] Fin {(finished-started).total_seconds():.1f}s OK:{ok} ERR:{err}")
    if err > 0 and ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    run()
