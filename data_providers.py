import asyncio
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf
import aiohttp

from config import CFG

TZ = ZoneInfo(CFG["TZ"])

class PriceProvider:
    """موحّد جلب الأسعار للفريمات المختلفة."""
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self

    async def __aexit__(self, *exc):
        if self.session:
            await self.session.close()

    async def get_recent(self, symbol: str, interval: str = "1m", lookback_minutes: int = 480) -> pd.DataFrame:
        period = "1d" if interval in ("1m", "2m") else "5d"
        data = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        if not isinstance(data, pd.DataFrame) or data.empty:
            return pd.DataFrame()
        data = data.rename(columns=str.title)
        try:
            data.index = data.index.tz_localize("UTC").tz_convert(TZ)
        except Exception:
            data.index = data.index.tz_convert(TZ)
        data = data.tail(int(lookback_minutes*1.5))
        return data

async def compact_timeframes(df_1m: pd.DataFrame) -> dict:
    out = {"1m": df_1m}
    if df_1m.empty:
        out["5m"] = pd.DataFrame()
        out["15m"] = pd.DataFrame()
        return out
    def resample(n):
        return df_1m.resample(f"{n}T").agg({
            "Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"
        }).dropna()
    out["5m"] = resample(5)
    out["15m"] = resample(15)
    return out
