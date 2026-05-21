import os, requests, feedparser
from datetime import datetime
import pytz

GOLD_API_KEY   = os.environ.get("GOLD_API_KEY")
MARKETAUX_KEY  = os.environ.get("MARKETAUX_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID")
RUN_TYPE       = os.environ.get("RUN_TYPE", "news")  # "price" or "news" or "digest"

KITCO_RSS = "https://www.kitco.com/rss/news.rss"
DUBAI_TZ  = pytz.timezone("Asia/Dubai")

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{8666914525:AAGGV-72NyVvHd80_BUvJsTf17knbDYgdHQ}/sendMessage",
        json={"-5025795531": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
        timeout=10
    )

def get_gold_price():
    r = requests.get(
        "https://www.goldapi.io/api/XAU/USD",
        headers={"x-access-token": GOLD_API_KEY},
        timeout=10
    )
    d = r.json()
    return d.get("price", 0), d.get("ch", 0), d.get("chp", 0)

def price_update(label):
    price, change, pct = get_gold_price()
    direction = "📈" if change >= 0 else "📉"
    sign = "+" if change >= 0 else ""
    feed = feedparser.parse(KITCO_RSS)
    headlines = "".join(f"{i}. {e.get('title','')}\n" for i, e in enumerate(feed.entries[:3], 1))
    now = datetime.now(DUBAI_TZ).strftime("%d %b %Y  %H:%M")
    send_telegram(
        f"🥇 <b>GOLD UPDATE — {label}</b>\n"
        f"🕐 {now} (Dubai)\n\n"
        f"💰 <b>XAU/USD:</b> ${price:,.2f}  "
        f"{direction} {sign}{change:.2f} ({sign}{pct:.2f}%)\n\n"
        f"📰 <b>Latest Headlines:</b>\n{headlines}"
    )

def breaking_news():
    feed = feedparser.parse(KITCO_RSS)
    new_items = []
    for e in feed.entries[:5]:
        title = e.get("title", "")
        link  = e.get("link", "")
        if title:
            new_items.append(f"📰 <b>KITCO</b>\n{title}\n🔗 {link}")
    try:
        r = requests.get(
            "https://api.marketaux.com/v1/news/all",
            params={"symbols": "XAUUSD", "filter_entities": "true",
                    "language": "en", "api_token": MARKETAUX_KEY, "limit": 3},
            timeout=10
        )
        for a in r.json().get("data", []):
            new_items.append(f"⚡ <b>{a.get('source','')}</b>\n{a.get('title','')}\n🔗 {a.get('url','')}")
    except: pass
    for item in new_items[:4]:
        send_telegram(item)

def daily_digest():
    feed = feedparser.parse(KITCO_RSS)
    headlines = "".join(f"{i}. {e.get('title','')}\n" for i, e in enumerate(feed.entries[:7], 1))
    now = datetime.now(DUBAI_TZ).strftime("%d %b %Y")
    send_telegram(
        f"🌅 <b>GOLD DAILY DIGEST</b> — {now}\n\n"
        f"📰 <b>Top Stories:</b>\n{headlines}\n"
        f"💡 Price updates at 10AM, 3PM, 9PM Dubai"
    )

# Run based on which workflow triggered this
if RUN_TYPE == "morning":   price_update("Morning 🌅")
elif RUN_TYPE == "afternoon": price_update("Afternoon ☀️")
elif RUN_TYPE == "evening":   price_update("Evening 🌙")
elif RUN_TYPE == "digest":    daily_digest()
elif RUN_TYPE == "news":      breaking_news()
