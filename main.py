from __future__ import annotations

import logging
import os
import random
import re
import threading
from datetime import datetime, timezone

import telebot
from dotenv import load_dotenv
from flask import Flask, jsonify

from arena.memory import MemoryStore
from arena.news import NewsService
from arena.personality import ArenaPersonality

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("project-arena")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

BOT_URL = os.getenv(
    "TELEGRAM_BOT_URL",
    "https://t.me/TwoTimeBackToBackBot",
).strip()

GROUP_URL = os.getenv(
    "TELEGRAM_GROUP_URL",
    "https://t.me/DrDisrespectMemeCoin",
).strip()

MEMORY_DB_PATH = os.getenv(
    "MEMORY_DB_PATH",
    "data/arena_memory.sqlite3",
).strip()

PORT = int(os.getenv("PORT", "8080"))

bot = telebot.TeleBot(TOKEN, parse_mode=None)
app = Flask(__name__)
news_service = NewsService()
memory = MemoryStore(MEMORY_DB_PATH)
personality = ArenaPersonality()


def touch(message):
    sender = message.from_user
    return memory.touch_user(
        telegram_id=sender.id,
        username=sender.username,
        first_name=sender.first_name,
        last_name=sender.last_name,
    )


def group_cta() -> str:
    if not GROUP_URL:
        return ""
    return f"\n\nJoin the Arena community: {GROUP_URL}"


@bot.message_handler(commands=["start"])
def start_command(message):
    profile, is_new = touch(message)
    name = memory.display_name(profile)
    greeting = personality.greeting(name, returning=not is_new)

    text = (
        f"🏟️ {greeting}\n\n"
        "Project Arena is a fan-made Doc-focused community bot with news, "
        "personal memory and occasional $DRD references.\n\n"
        "Commands:\n"
        "/arena — Arena energy\n"
        "/drd — $DRD community line\n"
        "/news — recent Doc-related headlines\n"
        "/profile — show what Arena knows about you\n"
        "/myname NAME — choose how Arena addresses you\n"
        "/forgetme — erase your Arena profile\n"
        "/about — project information"
        + group_cta()
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["arena"])
def arena_command(message):
    touch(message)
    bot.reply_to(message, personality.random_line("standard"))


@bot.message_handler(commands=["drd"])
def drd_command(message):
    touch(message)
    bot.reply_to(message, personality.random_line("drd"))


@bot.message_handler(commands=["profile"])
def profile_command(message):
    profile, _ = touch(message)
    name = memory.display_name(profile)

    bot.reply_to(
        message,
        (
            "🏆 Arena profile\n\n"
            f"Name: {name}\n"
            f"First seen: {profile.first_seen[:10]}\n"
            f"Last seen: {profile.last_seen[:10]}\n"
            f"Messages recorded: {profile.message_count}\n\n"
            "Use /myname NAME to change how Arena addresses you."
        ),
    )


@bot.message_handler(commands=["myname"])
def myname_command(message):
    profile, _ = touch(message)
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, "Use it like this: /myname Alex")
        return

    preferred_name = parts[1].strip()[:50]
    memory.set_preferred_name(profile.telegram_id, preferred_name)
    bot.reply_to(
        message,
        f"Locked in. The Arena will remember you as {preferred_name}.",
    )


@bot.message_handler(commands=["forgetme"])
def forgetme_command(message):
    memory.forget_user(message.from_user.id)
    bot.reply_to(
        message,
        "Your Arena profile and saved memories have been erased.",
    )


@bot.message_handler(commands=["news"])
def news_command(message):
    touch(message)

    try:
        items = news_service.latest(limit=5)
        if not items:
            bot.reply_to(message, "No fresh Arena intel is available right now.")
            return

        lines = ["📰 Latest Arena intel:"]
        for item in items:
            published = (
                item.published.strftime("%Y-%m-%d")
                if item.published
                else "date unknown"
            )
            lines.append(f"\n• {item.title}\n  {published} — {item.url}")

        bot.reply_to(message, "\n".join(lines))
    except Exception:
        logger.exception("News command failed")
        bot.reply_to(message, "Arena News is temporarily unavailable.")


@bot.message_handler(commands=["about"])
def about_command(message):
    touch(message)
    bot.reply_to(
        message,
        (
            "Project Arena is a fan-made community project. It is not affiliated "
            "with Dr Disrespect, Telegram, X, YouTube or any token issuer. "
            "Crypto references are community-themed and are not financial advice."
            + group_cta()
        ),
    )


NAME_PATTERNS = (
    re.compile(r"\bmy name is\s+([A-Za-zÀ-ÿ0-9_-]{2,30})", re.IGNORECASE),
    re.compile(r"\bcall me\s+([A-Za-zÀ-ÿ0-9_-]{2,30})", re.IGNORECASE),
)


@bot.message_handler(content_types=["text"])
def text_handler(message):
    profile, is_new = touch(message)
    text = (message.text or "").strip()
    lower = text.lower()

    for pattern in NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            preferred_name = match.group(1)
            memory.set_preferred_name(profile.telegram_id, preferred_name)
            bot.reply_to(
                message,
                f"Got it. The Arena will remember you as {preferred_name}.",
            )
            return

    if lower in {"hi", "hello", "hey", "yo", "hi doc", "hello doc"}:
        refreshed = memory.get_user(profile.telegram_id) or profile
        name = memory.display_name(refreshed)
        bot.reply_to(
            message,
            personality.greeting(name, returning=not is_new),
        )
        return

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

    if any(word in lower for word in trigger_words):
        category = (
            "challenge"
            if any(word in lower for word in challenge_words)
            else "standard"
        )
        response = personality.random_line(category)

        if GROUP_URL and random.random() < 0.12:
            response += group_cta()

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
