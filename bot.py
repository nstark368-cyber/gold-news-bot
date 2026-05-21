import os, requests, feedparser
from datetime import datetime
import pytz

GOLD_API_KEY   = os.environ.get("GOLD_API_KEY")
MARKETAUX_KEY  = os.environ.get("MARKETAUX_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID")
RUN_TYPE       = os.environ.get("RUN_TYPE", "news")

KITCO_RSS = "https://www.kitco.com/rss/news.rss"
DUBAI_TZ  = pytz.timezone("Asia/Dubai")

# ─── SEND TO TELEGRAM ────────────────────────────────────
def send_telegram(msg):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
        print(f"Telegram response: {r.status_code} — {r.text[:100]}")
    except Exception as e:
        print(f"Telegram error: {e}")

# ─── GOLD PRICE ──────────────────────────────────────────
def get_gold_price():
    try:
        r = requests.get(
            "https://www.goldapi.io/api/XAU/USD",
            headers={"x-access-token": GOLD_API_KEY},
            timeout=10
        )
        d = r.json()
        print(f"GoldAPI response: {d}")
        return d.get("price", 0), d.get("ch", 0), d.get("chp", 0)
    except Exception as e:
        print(f"GoldAPI error: {e}")
        return 0, 0, 0

# ─── KITCO RSS ───────────────────────────────────────────
def get_kitco_news(limit=5):
    try:
        feed = feedparser.parse(KITCO_RSS)
        print(f"Kitco RSS: fetched {len(feed.entries)} entries")
        return feed.entries[:limit]
    except Exception as e:
        print(f"Kitco error: {e}")
        return []

# ─── MARKETAUX NEWS ──────────────────────────────────────
def get_marketaux_news(limit=3):
    try:
        r = requests.get(
            "https://api.marketaux.com/v1/news/all",
            params={
                "symbols":         "XAUUSD",
                "filter_entities": "true",
                "language":        "en",
                "api_token":       MARKETAUX_KEY,
                "limit":           limit
            },
            timeout=10
        )
        data = r.json().get("data", [])
        print(f"Marketaux: fetched {len(data)} articles")
        return data
    except Exception as e:
        print(f"Marketaux error: {e}")
        return []

# ─── PRICE UPDATE (morning / afternoon / evening) ────────
def price_update(label):
    price, change, pct = get_gold_price()
    direction = "📈" if change >= 0 else "📉"
    sign      = "+" if change >= 0 else ""
    entries   = get_kitco_news(3)
    headlines = "".join(
        f"{i}. {e.get('title','')}\n"
        for i, e in enumerate(entries, 1)
    )
    now = datetime.now(DUBAI_TZ).strftime("%d %b %Y  %H:%M")
    send_telegram(
        f"🥇 <b>GOLD UPDATE — {label}</b>\n"
        f"🕐 {now} (Dubai)\n\n"
        f"💰 <b>XAU/USD:</b> ${price:,.2f}  "
        f"{direction} {sign}{change:.2f} ({sign}{pct:.2f}%)\n\n"
        f"📰 <b>Latest Headlines:</b>\n{headlines}"
    )

# ─── BREAKING NEWS (every 2 hours) ───────────────────────
def breaking_news():
    messages = []

    for e in get_kitco_news(4):
        title = e.get("title", "")
        link  = e.get("link",  "")
        if title:
            messages.append(
                f"📰 <b>KITCO</b>\n{title}\n🔗 {link}"
            )

    for a in get_marketaux_news(3):
        title = a.get("title", "")
        url   = a.get("url",   "")
        src   = a.get("source","")
        if title:
            messages.append(
                f"⚡ <b>{src}</b>\n{title}\n🔗 {url}"
            )

    if messages:
        for msg in messages[:5]:
            send_telegram(msg)
    else:
        print("No news items found.")

# ─── DAILY DIGEST (09:00 Dubai) ──────────────────────────
def daily_digest():
    entries   = get_kitco_news(7)
    headlines = "".join(
        f"{i}. {e.get('title','')}\n"
        for i, e in enumerate(entries, 1)
    )
    now = datetime.now(DUBAI_TZ).strftime("%d %b %Y")
    send_telegram(
        f"🌅 <b>GOLD DAILY DIGEST</b> — {now}\n\n"
        f"📰 <b>Top Stories Today:</b>\n{headlines}\n"
        f"💡 Price updates at:\n"
        f"   • 10:00 AM Dubai 🌅\n"
        f"   • 03:00 PM Dubai ☀️\n"
        f"   • 09:00 PM Dubai 🌙"
    )

# ─── MAIN ────────────────────────────────────────────────
print(f"Bot started — RUN_TYPE: {RUN_TYPE}")

if   RUN_TYPE == "morning":   price_update("Morning 🌅")
elif RUN_TYPE == "afternoon": price_update("Afternoon ☀️")
elif RUN_TYPE == "evening":   price_update("Evening 🌙")
elif RUN_TYPE == "digest":    daily_digest()
else:                         breaking_news()

print("Bot finished.")
