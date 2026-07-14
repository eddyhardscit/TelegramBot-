from __future__ import annotations
import logging, os, random, re, threading
from datetime import datetime, timezone
import telebot
from dotenv import load_dotenv
from flask import Flask, jsonify
from arena.memory import MemoryStore
from arena.news import NewsService
from arena.personality import ArenaPersonality
load_dotenv(); logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO")); logger=logging.getLogger("project-arena")
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
if not TOKEN: raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
BOT_URL=os.getenv("TELEGRAM_BOT_URL","https://t.me/TwoTimeBackToBackBot").strip(); GROUP_URL=os.getenv("TELEGRAM_GROUP_URL","https://t.me/DrDisrespectMemeCoin").strip(); PORT=int(os.getenv("PORT","8080"))
bot=telebot.TeleBot(TOKEN); app=Flask(__name__); news_service=NewsService(); memory=MemoryStore(os.getenv("MEMORY_DB_PATH","data/arena_memory.sqlite3")); personality=ArenaPersonality()
def touch(m):
    u=m.from_user; return memory.touch_user(u.id,u.username,u.first_name,u.last_name)
def group_cta(): return f"

Join the Arena community: {GROUP_URL}" if GROUP_URL else ""
@bot.message_handler(commands=["start"])
def start(m):
    p,is_new=touch(m); name=memory.display_name(p)
    bot.reply_to(m,f"🏟️ {personality.greeting(name,not is_new)}

Commands:
/arena
/drd
/news
/profile
/myname NAME
/forgetme
/about"+group_cta())
@bot.message_handler(commands=["arena"])
def arena(m): touch(m); bot.reply_to(m,personality.random_line("standard"))
@bot.message_handler(commands=["drd"])
def drd(m): touch(m); bot.reply_to(m,personality.random_line("drd"))
@bot.message_handler(commands=["profile"])
def profile(m):
    p,_=touch(m); bot.reply_to(m,f"🏆 Arena profile

Name: {memory.display_name(p)}
First seen: {p.first_seen[:10]}
Last seen: {p.last_seen[:10]}
Messages recorded: {p.message_count}")
@bot.message_handler(commands=["myname"])
def myname(m):
    p,_=touch(m); parts=(m.text or "").split(maxsplit=1)
    if len(parts)<2: bot.reply_to(m,"Use it like this: /myname Alex"); return
    memory.set_preferred_name(p.telegram_id,parts[1]); bot.reply_to(m,f"Locked in. The Arena will remember you as {parts[1][:50]}.")
@bot.message_handler(commands=["forgetme"])
def forgetme(m): memory.forget_user(m.from_user.id); bot.reply_to(m,"Your Arena profile and saved memories have been erased.")
@bot.message_handler(commands=["news"])
def news(m):
    touch(m)
    try:
        items=news_service.latest(5)
        if not items: bot.reply_to(m,"No fresh Arena intel is available right now."); return
        lines=["📰 Latest Arena intel:"]+[f"
• {x.title}
  {(x.published.strftime('%Y-%m-%d') if x.published else 'date unknown')} — {x.url}" for x in items]
        bot.reply_to(m,"
".join(lines))
    except Exception: logger.exception("news failed"); bot.reply_to(m,"Arena News is temporarily unavailable.")
@bot.message_handler(commands=["about"])
def about(m): touch(m); bot.reply_to(m,"Project Arena is fan-made and not affiliated with Dr Disrespect or any token issuer. Crypto references are not financial advice."+group_cta())
patterns=[re.compile(r"\bmy name is\s+([A-Za-zÀ-ÿ0-9_-]{2,30})",re.I),re.compile(r"\bcall me\s+([A-Za-zÀ-ÿ0-9_-]{2,30})",re.I)]
@bot.message_handler(content_types=["text"])
def text(m):
    p,is_new=touch(m); t=(m.text or "").strip(); low=t.lower()
    for pat in patterns:
        z=pat.search(t)
        if z: memory.set_preferred_name(p.telegram_id,z.group(1)); bot.reply_to(m,f"Got it. The Arena will remember you as {z.group(1)}."); return
    if low in {"hi","hello","hey","yo","hi doc","hello doc"}:
        p=memory.get_user(p.telegram_id) or p; bot.reply_to(m,personality.greeting(memory.display_name(p),not is_new)); return
    if any(w in low for w in ("doc","disrespect","arena","champions club","$drd"," drd","violence","speed","momentum")):
        cat="challenge" if any(w in low for w in ("suck","trash","noob","fraud","weak")) else "standard"; r=personality.random_line(cat)
        if GROUP_URL and random.random()<0.12: r+=group_cta()
        bot.reply_to(m,r)
@app.get("/")
def home(): return jsonify(project="Project Arena",status="online",timestamp=datetime.now(timezone.utc).isoformat())
@app.get("/health")
def health(): return jsonify(status="healthy"),200
def run_server(): app.run(host="0.0.0.0",port=PORT,use_reloader=False)
def main():
    threading.Thread(target=run_server,daemon=True).start(); bot.remove_webhook(); bot.infinity_polling(skip_pending=True,timeout=30,long_polling_timeout=30,allowed_updates=["message"])
if __name__=="__main__": main()
