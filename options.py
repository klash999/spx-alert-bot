from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass
class OptionCandidate:
    symbol: str
    strike: float
    side: str  # CALL/PUT
    delta: float
    bid: float
    ask: float
    spread: float
    volume: int
    oi: int
    expiry: str  # YYYY-MM-DD

@dataclass
class BestStrike:
    underlying: float
    call: Optional[OptionCandidate]
    put: Optional[OptionCandidate]

def pick_best_strike(options_df: pd.DataFrame, price: float,
                     dmin=0.2, dmax=0.35, max_spread=0.3,
                     min_vol=200, min_oi=500) -> BestStrike:
    if options_df is None or options_df.empty:
        return BestStrike(underlying=price, call=None, put=None)

    options_df = options_df.copy()
    options_df["spread"] = (options_df["ask"] - options_df["bid"]).clip(lower=0)

    def choose(side):
        sub = options_df[(options_df["side"]==side) &
                         (options_df["delta"].between(dmin, dmax, inclusive='both')) &
                         (options_df["spread"] <= max_spread) &
                         (options_df["volume"] >= min_vol) &
                         (options_df["oi"] >= min_oi)]
        if sub.empty:
            return None
        sub["kdist"] = (sub["strike"] - price).abs()
        sub = sub.sort_values(["kdist", "spread", "volume"], ascending=[True, True, False])
        r = sub.iloc[0]
        return OptionCandidate(symbol=r["symbol"], strike=float(r["strike"]), side=side,
                               delta=float(r["delta"]), bid=float(r["bid"]), ask=float(r["ask"]),
                               spread=float(r["spread"]), volume=int(r["volume"]), oi=int(r["oi"]),
                               expiry=str(r["expiry"]))

    return BestStrike(underlying=price, call=choose("CALL"), put=choose("PUT"))
