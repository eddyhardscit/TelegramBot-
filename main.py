import logging
import os
import random
import threading
from datetime import datetime, timezone

import telebot
from flask import Flask, jsonify

from arena.news import NewsService

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("project-arena")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

TELEGRAM_CHANNEL_URL = os.getenv("TELEGRAM_CHANNEL_URL", "").strip()
PORT = int(os.getenv("PORT", "8080"))

bot = telebot.TeleBot(TOKEN, parse_mode=None)
news_service = NewsService()
app = Flask(__name__)

ARENA_RESPONSES = [
    "Violence. Speed. Momentum. The Arena is open.",
    "The Two-Time energy is online. Welcome to Project Arena.",
    "Champions don't wait for momentum. They create it.",
    "$DRD is in the Arena. No promises, no weak talk—just community energy.",
    "Sunglasses on. Mullet locked. Arena mode activated.",
]

CHALLENGE_RESPONSES = [
    "You're not even on the minimap, kid.",
    "Cute attempt. The Arena has seen tougher competition in the warm-up lobby.",
    "Get a grip. Then step into the Arena.",
]


def channel_cta() -> str:
    if not TELEGRAM_CHANNEL_URL:
        return ""
    return f"\n\nJoin the Project Arena community: {TELEGRAM_CHANNEL_URL}"


@bot.message_handler(commands=["start"])
def start_command(message):
    text = (
        "🏟️ Welcome to Project Arena.\n\n"
        "A fan-made Telegram experience inspired by high-energy gaming culture, "
        "with Doc-related news, community chat and occasional $DRD references.\n\n"
        "Commands:\n"
        "/arena — Arena energy\n"
        "/drd — $DRD community line\n"
        "/news — recent Doc-related headlines\n"
        "/about — project information"
        + channel_cta()
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["arena", "drd"])
def arena_command(message):
    bot.reply_to(message, random.choice(ARENA_RESPONSES) + channel_cta())


@bot.message_handler(commands=["news"])
def news_command(message):
    try:
        items = news_service.latest(limit=5)
        if not items:
            bot.reply_to(message, "No fresh Arena intel is available right now.")
            return

        lines = ["📰 Latest Arena intel:"]
        for item in items:
            published = item.published.strftime("%Y-%m-%d") if item.published else "date unknown"
            lines.append(f"\n• {item.title}\n  {published} — {item.url}")
        bot.reply_to(message, "\n".join(lines))
    except Exception:
        logger.exception("News command failed")
        bot.reply_to(message, "Arena News is temporarily unavailable.")


@bot.message_handler(commands=["about"])
def about_command(message):
    bot.reply_to(
        message,
        "Project Arena is a fan-made community bot. It is not affiliated with Dr Disrespect, "
        "YouTube, X, Telegram or any token issuer. Crypto references are community-themed, "
        "not financial advice."
        + channel_cta(),
    )


@bot.message_handler(content_types=["text"])
def text_handler(message):
    text = (message.text or "").lower()
    trigger_words = (
        "doc",
        "disrespect",
        "arena",
        "champions club",
        "$drd",
        " drd",
        "violence",
        "speed",
        "momentum",
    )
    challenge_words = ("suck", "trash", "noob", "fraud", "weak")

    if any(word in text for word in trigger_words):
        pool = CHALLENGE_RESPONSES if any(word in text for word in challenge_words) else ARENA_RESPONSES
        response = random.choice(pool)
        # The Telegram CTA appears only occasionally to avoid repetitive promotion.
        if TELEGRAM_CHANNEL_URL and random.random() < 0.15:
            response += channel_cta()
        bot.reply_to(message, response)


@app.get("/")
def home():
    return jsonify(
        project="Project Arena",
        status="online",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
def health():
    return jsonify(status="healthy"), 200


def run_health_server() -> None:
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


def main() -> None:
    threading.Thread(target=run_health_server, daemon=True).start()
    logger.info("Project Arena started")
    bot.remove_webhook()
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30,
        allowed_updates=["message"],
    )


if __name__ == "__main__":
    main()
