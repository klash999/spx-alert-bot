# SPX Alert Bot (Telegram) — yfinance/SPY

بوت تنبيهات احترافي لـ SPX (يعتمد SPY للتطوير المجاني). يرسل:
- `/status` ملخص السعر + الأهداف + وقف الخسارة
- `/chart` شارت الساعة مع الدعوم/المقاومات والأهداف
- `/news` أهم الأخبار (اختياري عبر NEWSAPI)
- `/strike` اختيار أفضل Strike (0DTE) من سلاسل SPY

## تشغيل محلي
```bash
python -m venv .venv && source .venv/bin/activate  # أو .venv\Scripts\activate على ويندوز
pip install -r requirements.txt
cp .env.example .env  # تم تضمين .env جاهز أيضاً
python bot.py
```

## نشر على GitHub
```bash
git init
git add .
git commit -m "Initial release: SPX Alert Bot"
git branch -M main
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

## نشر على Render (Worker)
- اربط المستودع
- `render.yaml` سيضبط الأوامر تلقائياً
- أضف متغيرات البيئة من `.env` (أو اتركها ضمن .env إن كنت تبني من مصدر خاص)

> للتطوير المجاني نستخدم yfinance/SPY. لاحقاً يمكن الترقية إلى Polygon/Finnhub لخيارات SPX.
