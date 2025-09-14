import aiohttp
from datetime import datetime, timedelta, timezone
from typing import List
import yfinance as yf

from config import CFG

NEWS_KEY = CFG["API_KEYS"].get("newsapi", "")
FINNHUB_KEY = CFG["API_KEYS"].get("finnhub", "")

NEWS_QUERY = "(S&P 500 OR SPX OR Federal Reserve OR CPI OR FOMC OR Nvidia OR Apple OR Microsoft OR Treasury yields)"

def _fmt_lines(items: List[dict], limit: int = 5) -> List[str]:
    out = []
    for a in items[:limit]:
        title = a.get("title", "").strip()
        src = a.get("source", "") or a.get("source_name", "")
        url = a.get("url", "")
        if not title:
            continue
        line = f"📰 {title}"
        if src:
            line += f" — {src}"
        if url:
            line += f"\n{url}"
        out.append(line)
    return out or ["لا توجد أخبار متاحة حالياً."]

async def _via_newsapi(limit: int = 5, lang: str = "en"):
    if not NEWS_KEY:
        return None
    url = (
        "https://newsapi.org/v2/everything"
        f"?q={NEWS_QUERY}"
        f"&language={lang}&sortBy=publishedAt&pageSize={limit}&apiKey={NEWS_KEY}"
    )
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=20) as r:
                js = await r.json()
                arts = js.get("articles") or []
                items = [
                    {"title": a.get("title",""),
                     "source": (a.get("source",{}) or {}).get("name",""),
                     "url": a.get("url","")}
                    for a in arts
                ]
                return _fmt_lines(items, limit)
    except Exception as e:
        return [f"تعذّر جلب الأخبار عبر NewsAPI: {e}"]

async def _via_finnhub(limit: int = 5):
    if not FINNHUB_KEY:
        return None
    # أخبار عامة (أسرع من company-news المتطلب لنطاق تاريخ)
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=20) as r:
                js = await r.json()
                if not isinstance(js, list):
                    return ["تعذّر جلب الأخبار عبر Finnhub."]
                # فرز بالأحدث وتخفيف الضجيج على مواضيع السوق الأمريكي
                KEYWORDS = ("S&P", "SPX", "Fed", "FOMC", "CPI", "inflation", "Treasury", "Nvidia", "Apple", "Microsoft")
                filt = [x for x in js if any(k.lower() in (x.get("headline","")+x.get("summary","")).lower() for k in KEYWORDS)]
                items = [
                    {"title": x.get("headline",""),
                     "source": x.get("source",""),
                     "url": x.get("url","")}
                    for x in (filt or js)
                ]
                return _fmt_lines(items, limit)
    except Exception as e:
        return [f"تعذّر جلب الأخبار عبر Finnhub: {e}"]

def _via_yfinance(limit: int = 5):
    # لا تحتاج أي مفتاح — نجلب أخبار SPY و ^GSPC ونوحّدها
    try:
        items = []
        for sym in ("SPY", "^GSPC"):
            tk = yf.Ticker(sym)
            news = tk.news or []
            for n in news:
                t = n.get("title","")
                link = n.get("link","") or n.get("url","")
                src = (n.get("publisher","") or n.get("source","")).strip()
                # وقت النشر (يونكس) لاختيار الأحدث
                ts = n.get("providerPublishTime") or n.get("published_at")
                items.append({
                    "title": t, "url": link, "source": src, "ts": ts or 0
                })
        items = [x for x in items if x.get("title")]
        items.sort(key=lambda x: x.get("ts", 0), reverse=True)
        for x in items:
            # تطبيع الحقل للعارض
            x["source"] = x.get("source","")
        return _fmt_lines(items, limit)
    except Exception:
        return ["لا توجد أخبار متاحة حالياً."]

async def fetch_top_news(limit: int = 5, lang: str = "en"):
    """
    تفضيلات جلب الأخبار تلقائياً:
    1) NewsAPI إذا NEWSAPI_KEY موجود.
    2) Finnhub إذا FINNHUB_API_KEY موجود.
    3) YFinance بدون أي مفتاح.
    """
    # 1) NewsAPI
    if NEWS_KEY:
        r = await _via_newsapi(limit=limit, lang=lang)
        if r: return r

    # 2) Finnhub
    if FINNHUB_KEY:
        r = await _via_finnhub(limit=limit)
        if r: return r

    # 3) YFinance
    return _via_yfinance(limit=limit)
