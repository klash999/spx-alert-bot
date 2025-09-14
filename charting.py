import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import pandas as pd
from indicators import pivot_points, swing_levels

def plot_hourly_with_targets(df_hour: pd.DataFrame, targets: list, stop: float, title: str = "SPX H1") -> bytes:
    fig, ax = plt.subplots(figsize=(10,5))
    df = df_hour.copy()
    ax.plot(df.index, df['Close'], linewidth=1.5)

    ax.set_title(title)
    ax.set_xlabel('Time')
    ax.set_ylabel('Price')

    if len(df) >= 2:
        h = float(df['High'][-2])
        l = float(df['Low'][-2])
        c = float(df['Close'][-2])
        piv = pivot_points(h,l,c)
        for k,v in piv.items():
            ax.axhline(v, linestyle='--', linewidth=0.8)
            ax.text(df.index[0], v, k, fontsize=8, va='bottom')

    sw = swing_levels(df['Close'], lookback=min(200, len(df)))
    for t,price in sw:
        ax.axhline(price, alpha=0.3, linewidth=0.8)

    for i, tg in enumerate(targets, start=1):
        ax.axhline(tg, linewidth=1.2)
        ax.text(df.index[-1], tg, f'T{i}', fontsize=8)
    ax.axhline(stop, linewidth=1.2)
    ax.text(df.index[-1], stop, 'SL', fontsize=8)

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
