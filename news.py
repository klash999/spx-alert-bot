import aiohttp
from config import CFG

NEWS_KEY = CFG["API_KEYS"].get("newsapi", "")

async def fetch_top_news():
    if not NEWS_KEY:
        return ["ضع NEWSAPI_KEY في .env للحصول على الأخبار" ]
    q = "(S&P 500 OR SPX OR Federal Reserve OR CPI OR FOMC)"
    url = f"https://newsapi.org/v2/everything?q={q}&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_KEY}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=15) as r:
            js = await r.json()
            if not js.get("articles"):
                return ["لا توجد أخبار متاحة حالياً"]
            out = []
            for a in js["articles"]:
                out.append(f"📰 {a['title']} — {a.get('source',{}).get('name','')}\n{a.get('url','')}")
            return out[:5]
