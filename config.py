import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY   = os.environ.get("FMP_API_KEY", "")
EODHD_API_KEY = os.environ.get("EODHD_API_KEY", "")

_provider = os.environ.get("DATA_PROVIDER", "fmp").lower()

if _provider == "fmp" and not FMP_API_KEY:
    raise EnvironmentError(
        "FMP_API_KEY no configurada. Añadela en Railway Variables."
    )

from providers.fmp_provider   import FMPProvider
from providers.eodhd_provider import EODHDProvider

if _provider == "fmp":
    DATA_PROVIDER = FMPProvider(api_key=FMP_API_KEY)
elif _provider == "eodhd":
    DATA_PROVIDER = EODHDProvider(api_key=EODHD_API_KEY)
else:
    raise ValueError(f"DATA_PROVIDER desconocido: {_provider}")

# Ruta DB: /data en Railway, ./cache en local
_data_dir = pathlib.Path(os.environ.get("DATA_DIR", "./cache"))
_data_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = str(_data_dir / "scores.db")

TICKER_UNIVERSE_V1 = [
    "NVDA","META","LLY","CRWD","MSCI","AXON","ASML","NVO","ISRG",
    "FICO","ODFL","POOL","SHOP","MELI","CELH","DECK","FTNT","CDNS",
    "PANW","NOW","HUBS","TTD","DDOG","SNOW","SAP","TDG","RMD","VEEV",
]

FLASK_ENV    = os.environ.get("FLASK_ENV", "production")
PORT         = int(os.environ.get("PORT", "5000"))
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")
