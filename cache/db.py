import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager


def _path():
    from config import DB_PATH
    return DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS scores (
            ticker TEXT PRIMARY KEY, name TEXT, canon_score INTEGER,
            price REAL, change_pct REAL, w52_high REAL, ath_pct REAL,
            perf_1y REAL, rel_volume REAL, market_cap REAL,
            sma50 REAL, sma200 REAL, price_vs_sma50 REAL,
            price_vs_sma200 REAL, golden_cross INTEGER,
            roic REAL, roe REAL, roa REAL, net_margin REAL,
            gross_margin REAL, pe_ttm REAL, fwd_pe REAL, peg REAL,
            ps REAL, pb REAL, debt_equity REAL, current_ratio REAL,
            debt_ebitda REAL, eps_ttm REAL, eps_growth_yoy REAL,
            insider_own REAL, target_price REAL, sector TEXT,
            sales_cagr_3y REAL, sales_cagr_5y REAL,
            sales_latest_yoy REAL, batch_run_at TEXT, error TEXT
        );
        CREATE TABLE IF NOT EXISTS price_cache (
            ticker TEXT PRIMARY KEY, data_json TEXT, cached_at TEXT);
        CREATE TABLE IF NOT EXISTS fund_cache (
            ticker TEXT PRIMARY KEY, data_json TEXT, cached_at TEXT);
        CREATE TABLE IF NOT EXISTS sales_cache (
            ticker TEXT PRIMARY KEY, data_json TEXT, cached_at TEXT);
        CREATE TABLE IF NOT EXISTS batch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT, finished_at TEXT,
            tickers_ok INTEGER, tickers_err INTEGER, errors_json TEXT);
        """)
    print(f"[DB] {_path()}")


def upsert_score(data: dict):
    with get_conn() as c:
        cols = ", ".join(data.keys())
        ph   = ", ".join(["?"] * len(data))
        ups  = ", ".join([f"{k}=excluded.{k}" for k in data if k != "ticker"])
        c.execute(
            f"INSERT INTO scores ({cols}) VALUES ({ph}) "
            f"ON CONFLICT(ticker) DO UPDATE SET {ups}",
            list(data.values())
        )


def get_screener_results(filters: dict) -> list:
    conds, params = ["1=1", "(error IS NULL)"], []

    for fk, (col, op) in {
        "pe_max":           ("pe_ttm",        "<"),
        "fwd_pe_max":       ("fwd_pe",        "<"),
        "peg_max":          ("peg",           "<"),
        "ps_max":           ("ps",            "<"),
        "pb_max":           ("pb",            "<"),
        "roic_min":         ("roic",          ">"),
        "roe_min":          ("roe",           ">"),
        "roa_min":          ("roa",           ">"),
        "net_margin_min":   ("net_margin",    ">"),
        "gross_margin_min": ("gross_margin",  ">"),
        "debt_equity_max":  ("debt_equity",   "<"),
        "current_ratio_min":("current_ratio", ">"),
        "sales_3y_min":     ("sales_cagr_3y", ">"),
        "eps_growth_min":   ("eps_growth_yoy",">"),
        "insider_own_min":  ("insider_own",   ">"),
        "perf_1y_min":      ("perf_1y",       ">"),
        "rel_volume_min":   ("rel_volume",    ">"),
        "canon_score_min":  ("canon_score",  ">="),
    }.items():
        v = filters.get(fk)
        if v is not None:
            conds.append(f"({col} IS NOT NULL AND {col} {op} ?)")
            params.append(v)

    ath = filters.get("ath_pct_max")
    if ath is not None:
        conds.append("(ath_pct IS NOT NULL AND ath_pct >= ?)")
        params.append(-abs(ath))

    if filters.get("sector") not in (None, "all", ""):
        conds.append("(sector = ?)")
        params.append(filters["sector"])

    if filters.get("price_above_sma200"):
        conds.append("(price_vs_sma200 IS NOT NULL AND price_vs_sma200 > 0)")
    if filters.get("price_above_sma50"):
        conds.append("(price_vs_sma50 IS NOT NULL AND price_vs_sma50 > 0)")
    if filters.get("golden_cross"):
        conds.append("(golden_cross = 1)")

    limit = filters.get("limit", 200)
    with get_conn() as c:
        rows = c.execute(
            f"SELECT * FROM scores WHERE {' AND '.join(conds)} "
            f"ORDER BY canon_score DESC LIMIT ?",
            params + [limit]
        ).fetchall()
    return [dict(r) for r in rows]


def cache_get(table: str, ticker: str, ttl_min: int):
    with get_conn() as c:
        row = c.execute(
            f"SELECT data_json, cached_at FROM {table} WHERE ticker=?", [ticker]
        ).fetchone()
    if not row:
        return None
    if datetime.utcnow() - datetime.fromisoformat(row["cached_at"]) > timedelta(minutes=ttl_min):
        return None
    return json.loads(row["data_json"])


def cache_set(table: str, ticker: str, data: dict):
    with get_conn() as c:
        c.execute(
            f"INSERT OR REPLACE INTO {table} (ticker, data_json, cached_at) VALUES (?,?,?)",
            [ticker, json.dumps(data, default=str), datetime.utcnow().isoformat()]
        )


def log_batch(started, finished, ok, err, errors):
    with get_conn() as c:
        c.execute(
            "INSERT INTO batch_log (started_at,finished_at,tickers_ok,tickers_err,errors_json) "
            "VALUES (?,?,?,?,?)",
            [started.isoformat(), finished.isoformat(), ok, err, json.dumps(errors)]
        )
