import os
from dotenv import load_dotenv
load_dotenv()

CFG = {
    "TELEGRAM_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "TELEGRAM_ADMIN": int(os.getenv("TELEGRAM_ADMIN_ID", "0")),
    "TZ": os.getenv("TZ", "Asia/Riyadh"),
    "SYMBOL_INDEX": os.getenv("SYMBOL_INDEX", "^GSPC"),
    "SYMBOL_FUTURES": os.getenv("SYMBOL_FUTURES", "ES=F"),
    "SYMBOL_ETF": os.getenv("SYMBOL_ETF", "SPY"),
    "OPTIONS_PROVIDER": os.getenv("OPTIONS_PROVIDER", "yfinance"),
    "OPTIONS_UNDERLYING": os.getenv("OPTIONS_UNDERLYING", "SPY"),
    "INTERVALS": {
        "fast": int(os.getenv("INTERVAL_FAST", 60)),
        "med": int(os.getenv("INTERVAL_MED", 300)),
        "slow": int(os.getenv("INTERVAL_SLOW", 900)),
        "chart": int(os.getenv("CHART_REFRESH", 600)),
    },
    "RISK": {
        "stop": float(os.getenv("DEFAULT_STOP_PCT", 0.01)),
        "t1": float(os.getenv("DEFAULT_TARGET1_PCT", 0.005)),
        "t2": float(os.getenv("DEFAULT_TARGET2_PCT", 0.01)),
        "t3": float(os.getenv("DEFAULT_TARGET3_PCT", 0.015)),
    },
    "OPT": {
        "dmin": float(os.getenv("OPT_PREFERRED_DELTA_MIN", 0.20)),
        "dmax": float(os.getenv("OPT_PREFERRED_DELTA_MAX", 0.35)),
        "max_spread": float(os.getenv("OPT_MAX_SPREAD", 0.3)),
        "min_vol": int(os.getenv("OPT_MIN_VOLUME", 200)),
        "min_oi": int(os.getenv("OPT_MIN_OI", 500)),
    },
    "API_KEYS": {
        "polygon": os.getenv("POLYGON_API_KEY", ""),
        "finnhub": os.getenv("FINNHUB_API_KEY", ""),
        "iex": os.getenv("IEX_API_KEY", ""),
        "alphavantage": os.getenv("ALPHAVANTAGE_API_KEY", ""),
        "newsapi": os.getenv("NEWSAPI_KEY", ""),
    },
}
