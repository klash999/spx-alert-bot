import numpy as np
import pandas as pd

def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False).mean()

def rsi(series: pd.Series, n: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ma_up = up.ewm(com=n-1, adjust=False).mean()
    ma_down = down.ewm(com=n-1, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    return 100 - (100/(1+rs))

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def pivot_points(h, l, c):
    p = (h + l + c) / 3.0
    r1 = 2*p - l
    s1 = 2*p - c
    r2 = p + (h - l)
    s2 = p - (h - l)
    r3 = h + 2*(p - l)
    s3 = l - 2*(h - p)
    return {"P":p, "R1":r1, "S1":s1, "R2":r2, "S2":s2, "R3":r3, "S3":s3}

def swing_levels(close: pd.Series, lookback=50):
    if close.empty:
        return []
    s = close.tail(lookback)
    levels = []
    for i in range(2, len(s)-2):
        if s[i] == max(s[i-2:i+3]):
            levels.append((s.index[i], float(s[i])))
        if s[i] == min(s[i-2:i+3]):
            levels.append((s.index[i], float(s[i])))
    levels_sorted = sorted(levels, key=lambda x: x[1])
    pruned = []
    for t,price in levels_sorted:
        if not pruned or abs(price - pruned[-1][1]) > np.mean(s)*0.003:
            pruned.append((t,price))
    return pruned[-12:]
