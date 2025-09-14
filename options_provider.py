import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Literal
import pandas as pd
import yfinance as yf

from config import CFG

NY = ZoneInfo("America/New_York")
_DEF_SQRT2 = math.sqrt(2.0)

def _ndtr(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / _DEF_SQRT2))

def _bs_delta(spot: float, strike: float, t_years: float, iv: float, rate: float, side: Literal["CALL","PUT"]) -> float:
    if spot <= 0 or strike <= 0 or iv <= 0 or t_years <= 0:
        return 0.0
    d1 = (math.log(spot/strike) + (rate + 0.5*iv*iv)*t_years) / (iv*math.sqrt(t_years))
    return _ndtr(d1) if side == "CALL" else _ndtr(d1) - 1.0

class YFinanceOptionsProvider:
    def __init__(self, underlying: str = None):
        self.underlying = underlying or CFG.get("OPTIONS_UNDERLYING", "SPY")

    def _pick_same_day_expiry(self, tk: yf.Ticker) -> str:
        opts = tk.options or []
        if not opts:
            return ""
        today_ny = datetime.now(NY).date()
        same = [d for d in opts if d == today_ny.isoformat()]
        if same:
            return same[0]
        for d in opts:
            try:
                if datetime.fromisoformat(d).date() >= today_ny:
                    return d
            except Exception:
                continue
        return opts[0] if opts else ""

    def options_chain_df(self) -> pd.DataFrame:
        tk = yf.Ticker(self.underlying)
        expiry = self._pick_same_day_expiry(tk)
        if not expiry:
            return pd.DataFrame()
        chain = tk.option_chain(expiry)
        calls = chain.calls.copy()
        puts = chain.puts.copy()
        spot = tk.fast_info.get("last_price")
        if spot is None:
            hist = tk.history(period="1d")
            if hist.empty:
                return pd.DataFrame()
            spot = float(hist["Close"].iloc[-1])

        def prep(df, side):
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns=str.lower)
            df["side"] = side
            df["symbol"] = self.underlying
            df["expiry"] = expiry
            df["bid"] = df.get("bid", 0.0).fillna(0.0).astype(float)
            df["ask"] = df.get("ask", 0.0).fillna(0.0).astype(float)
            df["volume"] = df.get("volume", 0).fillna(0).astype(int)
            df["oi"] = df.get("openinterest", 0).fillna(0).astype(int)
            df["strike"] = df.get("strike").astype(float)

            now = datetime.now(NY)
            mkt_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            if now > mkt_close:
                mkt_close = now + timedelta(hours=6)
            t_years = max((mkt_close - now).total_seconds(), 60.0) / (365.0*24*3600)

            iv = df.get("impliedvolatility")
            iv = iv.fillna(0.25).astype(float) if iv is not None else pd.Series([0.25]*len(df))
            df["delta"] = [abs(_bs_delta(spot, k, t_years, max(v, 0.01), 0.0, side)) for k, v in zip(df["strike"], iv)]
            df = df[(df["ask"] >= df["bid"]) & (df["ask"] > 0)]
            return df[["symbol","strike","side","delta","bid","ask","volume","oi","expiry"]]

        out = pd.concat([prep(calls, "CALL"), prep(puts, "PUT")], ignore_index=True)
        return out

    def spot_price(self) -> float:
        tk = yf.Ticker(self.underlying)
        p = tk.fast_info.get("last_price")
        if p:
            return float(p)
        h = tk.history(period="1d").tail(1)
        return float(h["Close"].iloc[-1]) if not h.empty else float("nan")
