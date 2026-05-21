import os, time, requests, feedparser
from datetime import datetime
import schedule

# ── CONFIG (set these in Render environment variables) ──
GOLD_API_KEY    = os.environ.get("GOLD_API_KEY")
MARKETAUX_KEY   = os.environ.get("MARKETAUX_KEY")
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT   = os.environ.get("TELEGRAM_CHAT_ID")
KITCO_RSS       = "https://www.kitco.com/rss/news.rss"

sent_headlines  = set()  # track already-sent news

# ────────────────────────────────────────────────────────
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT,
        "text": msg,
        "parse_mode": "HTML"
    })

# ────────────────────────────────────────────────────────
def get_gold_price():
    r = requests.get(
        "https://www.goldapi.io/api/XAU/USD",
        headers={"x-access-token": GOLD_API_KEY}
    )
    d = r.json()
    return d.get("price", 0), d.get("ch", 0), d.get("chp", 0)

# ────────────────────────────────────────────────────────
def check_breaking_news():
    """Runs every 15 minutes — sends only NEW headlines"""
    global sent_headlines

    # 1. Kitco RSS (always free, no limit)
    feed = feedparser.parse(KITCO_RSS)
    for entry in feed.entries[:5]:
        title = entry.get("title", "")
        link  = entry.get("link", "")
        if title and title not in sent_headlines:
            sent_headlines.add(title)
            send_telegram(
                f"📰 <b>KITCO BREAKING</b>\n"
                f"{title}\n"
                f"🔗 {link}"
            )
            time.sleep(1)

    # 2. Marketaux financial news (gold/commodities)
    try:
        r = requests.get(
            "https://api.marketaux.com/v1/news/all",
            params={
                "symbols": "XAUUSD",
                "filter_entities": "true",
                "language": "en",
                "api_token": MARKETAUX_KEY,
                "limit": 3
            }
        )
        articles = r.json().get("data", [])
        for a in articles:
            title = a.get("title", "")
            url   = a.get("url", "")
            src   = a.get("source", "")
            if title and title not in sent_headlines:
                sent_headlines.add(title)
                send_telegram(
                    f"⚡ <b>BREAKING | {src}</b>\n"
                    f"{title}\n"
                    f"🔗 {url}"
                )
                time.sleep(1)
    except Exception as e:
        print(f"Marketaux error: {e}")

# ────────────────────────────────────────────────────────
def daily_summary():
    """Runs once at 7:00 AM UTC — full digest"""
    price, change, change_pct = get_gold_price()

    direction = "📈" if change >= 0 else "📉"
    sign      = "+" if change >= 0 else ""

    # Top 5 news from Kitco
    feed = feedparser.parse(KITCO_RSS)
    news_lines = ""
    for i, entry in enumerate(feed.entries[:5], 1):
        news_lines += f"{i}. {entry.get('title','')}\n"

    msg = (
        f"🌅 <b>GOLD DAILY DIGEST</b> — {datetime.utcnow().strftime('%d %b %Y')}\n\n"
        f"💰 <b>XAU/USD:</b> ${price:,.2f}  "
        f"{direction} {sign}{change:.2f} ({sign}{change_pct:.2f}%)\n\n"
        f"📰 <b>Top Headlines:</b>\n"
        f"{news_lines}\n"
        f"⏰ Next update: Tomorrow 7:00 AM UTC"
    )
    send_telegram(msg)

# ────────────────────────────────────────────────────────
# SCHEDULER
schedule.every(15).minutes.do(check_breaking_news)
schedule.every().day.at("07:00").do(daily_summary)

print("✅ Gold News Bot started!")
send_telegram("🤖 <b>Gold News Bot is LIVE!</b>\nBreaking news every 15min\nDaily digest at 7AM UTC")

# Run immediately on startup
check_breaking_news()
daily_summary()

while True:
    schedule.run_pending()
    time.sleep(30)