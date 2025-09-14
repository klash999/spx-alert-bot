import asyncio
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import CFG
from data_providers import PriceProvider, compact_timeframes
from indicators import rsi, macd
from charting import plot_hourly_with_targets
from options import pick_best_strike
from news import fetch_top_news
from utils import now_local

INDEX_SYMBOL = CFG["SYMBOL_INDEX"]

async def fetch_prices():
    async with PriceProvider() as prov:
        df_1m = await prov.get_recent(INDEX_SYMBOL, interval="1m", lookback_minutes=600)
        packs = await compact_timeframes(df_1m)
        return packs

def compute_setup(df_1m: pd.DataFrame):
    if df_1m.empty or len(df_1m) < 50:
        return None
    close = df_1m['Close']
    r = rsi(close)
    m, s, h = macd(close)
    last = close.iloc[-1]

    t1 = last * (1 + CFG['RISK']['t1'])
    t2 = last * (1 + CFG['RISK']['t2'])
    t3 = last * (1 + CFG['RISK']['t3'])
    sl = last * (1 - CFG['RISK']['stop'])

    bias = "محايد"
    if m.iloc[-1] > s.iloc[-1] and r.iloc[-1] > 55:
        bias = "صاعد"
    elif m.iloc[-1] < s.iloc[-1] and r.iloc[-1] < 45:
        bias = "هابط"

    return {
        "price": float(last),
        "targets": [float(t1), float(t2), float(t3)],
        "stop": float(sl),
        "bias": bias
    }

async def make_chart(df_1m: pd.DataFrame, targets: list, stop: float) -> bytes:
    df_h = df_1m.resample('60T').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    return plot_hourly_with_targets(df_h, targets, stop, title="SPX H1 — Targets & S/R")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً 👋\n\nهذا بوت تنبيهات SPX الاحترافي.\n"
        "الأوامر:\n"
        "/start — هذه الرسالة\n"
        "/status — ملخص السوق\n"
        "/chart — شارت الساعة مع الأهداف\n"
        "/news — أهم الأخبار المؤثرة\n"
        "/strike — اختيار Strike (0DTE) إرشادي"
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    packs = await fetch_prices()
    df1 = packs.get('1m', pd.DataFrame())
    st = compute_setup(df1) or {"price":0.0,"targets":[],"stop":0.0,"bias":"لا بيانات"}
    if not st["targets"]:
        await update.message.reply_text("لا تتوفر بيانات كافية الآن")
        return
    text = (
        f"⏱ {now_local():%Y-%m-%d %H:%M} ({CFG['TZ']})\n"
        f"📈 السعر: {st['price']:.2f} \n"
        f"🎯 الأهداف: " + ", ".join([f"T{i+1}:{t:.2f}" for i,t in enumerate(st['targets'])]) + "\n"
        f"🛡 وقف الخسارة: {st['stop']:.2f}\n"
        f"📊 الانحياز: {st['bias']}\n"
    )
    await update.message.reply_text(text)

async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    packs = await fetch_prices()
    df1 = packs.get('1m', pd.DataFrame())
    st = compute_setup(df1)
    if not st:
        await update.message.reply_text("لا تتوفر بيانات كافية الآن")
        return
    img_bytes = await make_chart(df1, st['targets'], st['stop'])
    await update.message.reply_photo(photo=img_bytes, caption="شارت الساعة مع الأهداف و S/R")

async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    items = await fetch_top_news()
    await update.message.reply_text("\n\n".join(items))

async def cmd_strike(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from options_provider import YFinanceOptionsProvider
    prov = YFinanceOptionsProvider(CFG.get("OPTIONS_UNDERLYING", "SPY"))
    df = prov.options_chain_df()
    if df is None or df.empty:
        await update.message.reply_text("تعذر جلب سلاسل الخيارات حالياً — جرّب لاحقاً")
        return
    price = prov.spot_price()

    best = pick_best_strike(
        df, price,
        dmin=CFG['OPT']['dmin'], dmax=CFG['OPT']['dmax'],
        max_spread=CFG['OPT']['max_spread'], min_vol=CFG['OPT']['min_vol'], min_oi=CFG['OPT']['min_oi']
    )

    def fmt(c):
        if c is None: return "—"
        return f"{c.side} {c.strike} | Δ={c.delta:.2f} | bid/ask={c.bid:.2f}/{c.ask:.2f} | vol/oi={c.volume}/{c.oi}"

    msg = (
        f"💡 أفضل Strike (0DTE) إرشادي عند سعر {price:.2f} ({CFG.get('OPTIONS_UNDERLYING','SPY')}):\n"
        f"Calls: {fmt(best.call)}\n"
        f"Puts:  {fmt(best.put)}\n"
        "\n⚠️ المصدر: yfinance (سلاسل SPY). للانتقال إلى Polygon/Finnhub أضف مفتاح API وعدّل OPTIONS_PROVIDER."
    )
    await update.message.reply_text(msg)

def main():
    token = CFG["TELEGRAM_TOKEN"]
    if not token:
        raise SystemExit("ضع TELEGRAM_BOT_TOKEN في .env")
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("chart", cmd_chart))
    application.add_handler(CommandHandler("news", cmd_news))
    application.add_handler(CommandHandler("strike", cmd_strike))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
