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
    return f"\n\nJoin the Arena community: {GROUP_URL}" if GROUP_URL else ""


def humanize_key(key: str) -> str:
    labels = {
        "favorite_game": "Favourite game",
        "favorite_topic": "Favourite topic",
        "gaming_platform": "Gaming platform",
        "follows_doc_since": "Following the Doc since",
    }
    return labels.get(key, key.replace("_", " ").title())


def clean_value(value: str) -> str:
    return value.strip().strip(" .,!?:;\"'")[:100]


def extract_memory(text: str) -> tuple[str, str] | None:
    patterns = (
        ("favorite_game", re.compile(r"\bmy favou?rite game is\s+(.+)$", re.I)),
        ("favorite_topic", re.compile(r"\bmy favou?rite topic is\s+(.+)$", re.I)),
        ("gaming_platform", re.compile(r"\bi (?:mostly )?play on\s+(.+)$", re.I)),
        ("follows_doc_since", re.compile(r"\bi(?:'ve| have) followed (?:the )?doc since\s+(.+)$", re.I)),
    )
    for key, pattern in patterns:
        match = pattern.search(text.strip())
        if match:
            value = clean_value(match.group(1))
            if value:
                return key, value
    return None


def immersive_greeting(name: str, is_new: bool, previous_last_seen: str | None) -> str:
    if is_new:
        return (
            f"🏟️ Welcome to the Arena, {name}.\n\n"
            "Violence. Speed. Momentum.\n"
            "Don't embarrass yourself."
        )

    elapsed_line = ""
    if previous_last_seen:
        try:
            previous = datetime.fromisoformat(previous_last_seen)
            days = max(0, (datetime.now(timezone.utc) - previous).days)
            if days >= 2:
                elapsed_line = f"\n{days} days away from the Arena."
        except ValueError:
            pass

    return (
        f"🏟️ Welcome back, {name}.\n\n"
        f"The Arena remembers you.{elapsed_line}\n"
        "What's today's mission?"
    )


@bot.message_handler(commands=["start"])
def start_command(message):
    profile, is_new, previous_last_seen = touch(message)
    name = memory.display_name(profile)
    text = (
        immersive_greeting(name, is_new, previous_last_seen)
        + "\n\nCommands:\n"
        "/arena — Arena energy\n"
        "/drd — $DRD community line\n"
        "/news — recent Doc-related headlines\n"
        "/profile — your Arena profile\n"
        "/memory — what Arena remembers\n"
        "/myname NAME — choose your Arena name\n"
        "/forget KEY — erase one saved preference\n"
        "/forgetme — erase your full profile\n"
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
    profile, _, _ = touch(message)
    name = memory.display_name(profile)
    bot.reply_to(
        message,
        (
            "🏆 Arena profile\n\n"
            f"Name: {name}\n"
            f"First seen: {profile.first_seen[:10]}\n"
            f"Last seen: {profile.last_seen[:10]}\n"
            f"Messages recorded: {profile.message_count}\n\n"
            "Use /memory to see saved preferences."
        ),
    )


@bot.message_handler(commands=["memory"])
def memory_command(message):
    profile, _, _ = touch(message)
    name = memory.display_name(profile)
    saved = memory.list_memories(profile.telegram_id)

    if not saved:
        bot.reply_to(
            message,
            (
                f"🧠 Arena Memory — {name}\n\n"
                "I remember your profile, but no preferences yet.\n\n"
                "Try telling me:\n"
                "My favorite game is PUBG\n"
                "I play on PlayStation\n"
                "I've followed the Doc since 2017"
            ),
        )
        return

    lines = [f"🧠 Arena Memory — {name}", "", "I remember:"]
    for key, value in saved:
        lines.append(f"• {humanize_key(key)}: {value}")
    lines.extend(["", "Use /forget KEY to erase one item.", "Example: /forget favorite_game"])
    bot.reply_to(message, "\n".join(lines))


@bot.message_handler(commands=["myname"])
def myname_command(message):
    profile, _, _ = touch(message)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, "Use it like this: /myname Alex")
        return
    preferred_name = clean_value(parts[1])[:50]
    memory.set_preferred_name(profile.telegram_id, preferred_name)
    bot.reply_to(message, f"Locked in. The Arena will remember you as {preferred_name}.")


@bot.message_handler(commands=["forget"])
def forget_command(message):
    profile, _, _ = touch(message)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, "Use it like this: /forget favorite_game")
        return
    key = parts[1].strip().lower()
    if memory.forget_memory(profile.telegram_id, key):
        bot.reply_to(message, f"Memory erased: {humanize_key(key)}.")
    else:
        bot.reply_to(message, "I don't have that memory stored.")


@bot.message_handler(commands=["forgetme"])
def forgetme_command(message):
    memory.forget_user(message.from_user.id)
    bot.reply_to(message, "Your Arena profile and saved memories have been erased.")


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
            published = item.published.strftime("%Y-%m-%d") if item.published else "date unknown"
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
    re.compile(r"\bmy name is\s+([A-Za-zÀ-ÿ0-9_-]{2,30})", re.I),
    re.compile(r"\bcall me\s+([A-Za-zÀ-ÿ0-9_-]{2,30})", re.I),
)


@bot.message_handler(content_types=["text"])
def text_handler(message):
    profile, is_new, previous_last_seen = touch(message)
    text = (message.text or "").strip()
    lower = text.lower()

    for pattern in NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            preferred_name = match.group(1)
            memory.set_preferred_name(profile.telegram_id, preferred_name)
            bot.reply_to(message, f"Got it. The Arena will remember you as {preferred_name}.")
            return

    extracted = extract_memory(text)
    if extracted:
        key, value = extracted
        memory.remember(profile.telegram_id, key, value)
        memory.remember(profile.telegram_id, "context_last_subject", value)
        bot.reply_to(message, f"Locked in. I'll remember your {humanize_key(key).lower()}: {value}.")
        return

    if lower in {
        "what is my favorite game?",
        "what's my favorite game?",
        "do you remember my favorite game?",
        "what is my favourite game?",
        "what's my favourite game?",
        "do you remember my favourite game?",
    }:
        game = memory.recall(profile.telegram_id, "favorite_game")
        if game:
            bot.reply_to(message, f"Your favourite game is {game}. The Arena remembers.")
        else:
            bot.reply_to(message, "You haven't told me your favourite game yet.")
        return

    if lower in {"should i buy it?", "should i get it?", "is it worth buying?"}:
        subject = memory.recall(profile.telegram_id, "context_last_subject")
        if subject:
            bot.reply_to(
                message,
                f"If you mean {subject}, I remember the subject—but I need the platform, price or edition before I give you a serious verdict.",
            )
        else:
            bot.reply_to(message, "Tell me what game or product you mean first.")
        return

    if lower in {"hi", "hello", "hey", "yo", "hi doc", "hello doc"}:
        refreshed = memory.get_user(profile.telegram_id) or profile
        bot.reply_to(
            message,
            immersive_greeting(memory.display_name(refreshed), is_new, previous_last_seen),
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
        category = "challenge" if any(word in lower for word in challenge_words) else "standard"
        response = personality.random_line(category)
        if GROUP_URL and random.random() < 0.12:
            response += group_cta()
        bot.reply_to(message, response)


@app.get("/")
def home():
    return jsonify(
        project="Project Arena",
        version="1.1",
        status="online",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
def health():
    return jsonify(status="healthy", version="1.1"), 200


def run_health_server() -> None:
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


def main() -> None:
    threading.Thread(target=run_health_server, daemon=True).start()
    logger.info("Project Arena v1.1 started")
    bot.remove_webhook()
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30,
        allowed_updates=["message"],
    )


if __name__ == "__main__":
    main()
