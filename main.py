import telebot
import random
import threading
import json
import re
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string, request
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Message, BotStats, ErrorLog
from analytics import BotAnalytics
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TOKEN:
    TOKEN = TOKEN.strip()  # Remove any whitespace
    # Extract only the token part if there's extra text
    import re
    token_match = re.search(r'\b\d+:[A-Za-z0-9_-]+\b', TOKEN)
    if token_match:
        TOKEN = token_match.group()
    elif ' ' in TOKEN or len(TOKEN) != 46:  # Telegram tokens are exactly 46 characters
        print(f"Invalid token format. Expected format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        print(f"Received token length: {len(TOKEN)}")
        print(f"Token preview: {TOKEN[:20]}...")
        exit(1)

try:
    bot = telebot.TeleBot(TOKEN)
except Exception as e:
    print(f"Error initializing bot: {e}")
    print("Please check your TELEGRAM_BOT_TOKEN in Replit Secrets")
    exit(1)

# Enhanced response categories for varied personality

# Standard cocky responses - classic Dr Disrespect energy
standard_responses = [
    "⚔️ Violence. ⚡ Speed. 💣 Momentum. That's the $DRD way.",
    "You can't handle the Two-Time energy. $DRD only.",
    "Still stuck in the past? The future is $DRD, baby.",
    "Dominate or step aside. $DRD.",
    "They play checkers. I play $DRD-level chess.",
    "Welcome to the Champions Club. Grab your $DRD.",
    "They follow charts. I bring the flame. $DRD.",
    "🎯 Precision. 💪 Power. 👑 $DRD dominance.",
    "The Arena awaits champions, not wannabes. $DRD time.",
    "Ethiopian poisonous caterpillar speed with $DRD gains.",
    "Slick Daddy Club members know: $DRD or nothing.",
    "Bulletproof mullet, laser focus, $DRD profits.",
    "🔥 Back-to-back. 🏆 Two-Time. 💰 $DRD Champion.",
    "The mustache doesn't lie. $DRD delivers.",
    "Gillette: The best a man can get. $DRD: The best gains you'll see."
]

# Ultra cocky responses - maximum confidence
ultra_cocky_responses = [
    "I'm the face of $DRD, the franchise player, the guy!",
    "Six-foot-eight frame, 37-inch vertical leap, $DRD gains.",
    "Google prototype scopes with built-in $DRD tracking.",
    "The 1993, 1994 Blockbuster video game champion holds $DRD.",
    "Lamborghini mercy, $DRD no mercy on paper hands.",
    "Think about it: blonde-banged punk kids can't handle $DRD pressure.",
    "Diamond hands, diamond heart, $DRD rocket ship.",
    "I don't just break records, I break $DRD resistance levels.",
    "The Two-Time doesn't chase pumps. $DRD chases me.",
    "Get a grip, grip the $DRD, and watch magic happen.",
    "🕶️ Sunglasses indoors because $DRD's future is too bright.",
    "Violence. Speed. Momentum. And $DRD moonshots, baby!",
    "The Doc doesn't predict markets. Markets follow $DRD energy."
]

# Dismissive responses - for doubters and haters
dismissive_responses = [
    "You're not even on the minimap, kid. $DRD holders see the whole map.",
    "Cute portfolio. Come back when you've joined the $DRD Champions Club.",
    "You better pray the Doc doesn't respond with $DRD headshots.",
    "That's adorable. $DRD plays in a different league.",
    "You're talking to the face of $DRD. Know your place.",
    "The Doc doesn't argue with ants. $DRD speaks for itself.",
    "You're swimming in the kiddie pool. $DRD is deep ocean.",
    "Participation trophy mentality won't get you $DRD gains.",
    "You're stuck in bronze rank. $DRD is championship tier.",
    "Keep watching from the sidelines while $DRD dominates.",
    "You're playing checkers while $DRD plays 4D chess.",
    "That's some JV-level thinking. $DRD is varsity only."
]

# Dominant responses - pure power moves
dominant_responses = [
    "The Arena belongs to $DRD champions. Period.",
    "I don't just hold $DRD. I AM the $DRD energy.",
    "When $DRD moves, mountains move. When I speak, markets listen.",
    "The Champions Club doesn't follow trends. We set them with $DRD.",
    "Peak performance isn't a goal, it's the $DRD standard.",
    "I don't chase bags. $DRD bags chase me.",
    "The Two-Time doesn't do second place. $DRD to the moon.",
    "Authority. Respect. $DRD dominance. That's the trinity.",
    "I built the $DRD empire with these two hands.",
    "The mustache speaks: $DRD or stay home.",
    "Championship DNA flows through every $DRD transaction.",
    "The Doc commands respect. $DRD demands attention.",
    "Violence, speed, momentum - the $DRD holy trinity.",
    "I don't trade $DRD. I orchestrate symphonies."
]

# Challenge responses - for insults and confrontation
challenge_responses = [
    "You're talking to the face of $DRD. Know your place.",
    "You better pray the Doc doesn't respond with headshots.",
    "Cute insult. Come back when you've joined the Champions Club.",
    "You're not even on the minimap, kid.",
    "The Doc doesn't argue. He eliminates with $DRD power.",
    "That's some serious disrespect. $DRD will handle this.",
    "You just poked the Ethiopian poisonous caterpillar. $DRD time.",
    "The mustache is twitching. $DRD is about to explode.",
    "You want smoke? $DRD brings the whole volcano.",
    "The Arena doesn't tolerate weakness. Neither does $DRD.",
    "You just signed your own elimination papers, punk kid.",
    "The Champions Club has a zero-tolerance policy for punks."
]

# Commands
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        # Log user activity
        user = BotAnalytics.log_user_activity(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        welcome_msg = (
            "🎮 Welcome to the Champions Club! 😎💣\n\n"
            "I'm the Two-Time, back-to-back Blockbuster Video Game Champion, "
            "and your gateway to $DRD dominance!\n\n"
            "Commands:\n"
            "/drd - Get some Champions Club energy\n"
            "/arena - Enter the competitive zone\n"
            "/club - Join the exclusive club\n"
            "/stats - View your Champions Club stats\n\n"
            "The Arena awaits, champion. Let's dominate! 🏆"
        )
        bot.reply_to(message, welcome_msg)
        
        # Log command usage
        if user:
            BotAnalytics.log_message(
                user=user,
                message_text=message.text,
                message_type="command",
                response_category="welcome",
                bot_responded=True
            )
    except Exception as e:
        BotAnalytics.log_error("START_COMMAND", str(e))

@bot.message_handler(commands=['drd'])
def send_drd(message):
    try:
        user = BotAnalytics.log_user_activity(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Mix responses from different categories for variety
        all_responses = standard_responses + ultra_cocky_responses
        response = random.choice(all_responses)
        bot.reply_to(message, response)
        
        if user:
            BotAnalytics.log_message(
                user=user,
                message_text=message.text,
                message_type="command",
                response_category="drd_mixed",
                bot_responded=True
            )
    except Exception as e:
        BotAnalytics.log_error("DRD_COMMAND", str(e))

@bot.message_handler(commands=['arena'])
def send_arena(message):
    try:
        user = BotAnalytics.log_user_activity(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        arena_responses = [
            "🏟️ The Arena is calling, champion. $DRD holders only.",
            "⚔️ Step into the Arena where legends are made. $DRD energy required.",
            "🎯 Arena mode activated. Time to show them $DRD dominance.",
            "🔥 The competitive spirit flows through $DRD veins.",
            "🏆 Arena champions don't just play. They hold $DRD."
        ]
        response = random.choice(arena_responses)
        bot.reply_to(message, response)
        
        if user:
            BotAnalytics.log_message(
                user=user,
                message_text=message.text,
                message_type="command",
                response_category="arena",
                bot_responded=True
            )
    except Exception as e:
        BotAnalytics.log_error("ARENA_COMMAND", str(e))

@bot.message_handler(commands=['club'])
def send_club(message):
    try:
        user = BotAnalytics.log_user_activity(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        club_responses = [
            "🏛️ The Champions Club is exclusive. $DRD is your membership card.",
            "👑 Welcome to the elite. $DRD holders get VIP treatment.",
            "🤝 The Slick Daddy Club recognizes $DRD excellence.",
            "🌟 Championship DNA verified. $DRD membership activated.",
            "🎭 The mustache approves. You're Champions Club material with $DRD."
        ]
        response = random.choice(club_responses)
        bot.reply_to(message, response)
        
        if user:
            BotAnalytics.log_message(
                user=user,
                message_text=message.text,
                message_type="command",
                response_category="club",
                bot_responded=True
            )
    except Exception as e:
        BotAnalytics.log_error("CLUB_COMMAND", str(e))

@bot.message_handler(commands=['stats'])
def send_stats(message):
    try:
        user = BotAnalytics.log_user_activity(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        if user:
            user_obj = User.query.filter_by(telegram_id=message.from_user.id).first()
            if user_obj:
                stats_msg = (
                    f"🏆 Champions Club Stats for {user_obj.first_name or 'Champion'}:\n\n"
                    f"📊 Total Messages: {user_obj.total_messages}\n"
                    f"📅 Member Since: {user_obj.created_at.strftime('%B %d, %Y')}\n"
                    f"⚡ Last Activity: {user_obj.last_activity.strftime('%B %d, %Y')}\n"
                    f"🎯 Status: Champions Club Member\n\n"
                    f"Violence. Speed. Momentum. You're living the $DRD lifestyle! 🔥"
                )
            else:
                stats_msg = "🎮 Welcome to the Champions Club! Use other commands to build your stats."
        else:
            stats_msg = "⚠️ Unable to retrieve stats. Try again, champion!"
            
        bot.reply_to(message, stats_msg)
        
        if user:
            BotAnalytics.log_message(
                user=user,
                message_text=message.text,
                message_type="command",
                response_category="stats",
                bot_responded=True
            )
    except Exception as e:
        BotAnalytics.log_error("STATS_COMMAND", str(e))

# Enhanced keyword detection system
# Gaming and streaming keywords
gaming_keywords = ['doc', 'disrespect', 'arena', 'champions club', 'two time', '2x', 'blockbuster', 
                  'gaming', 'stream', 'twitch', 'youtube', 'esports', 'competitive', 'fps']

# Dr Disrespect signature terms
signature_keywords = ['violence', 'speed', 'momentum', 'mustache', 'mullet', 'sunglasses', 
                     'ethiopian', 'caterpillar', 'gillette', 'lamborghini', 'prototype', 'slick daddy']

# Crypto and DRD related terms
crypto_keywords = ['drd', 'crypto', 'token', 'moon', 'diamond hands', 'paper hands', 'hodl', 
                  'pump', 'dump', 'gains', 'chart', 'portfolio', 'bullish', 'bearish']

# Negative/challenge keywords
challenge_keywords = ['better', 'suck', 'noob', 'trash', 'bad', 'weak', 'loser', 'scrub', 
                     'bronze', 'silver', 'amateur', 'wannabe', 'fake', 'fraud', 'overrated']

# Positive/hype keywords  
hype_keywords = ['champion', 'legend', 'elite', 'pro', 'god', 'king', 'beast', 'dominate', 
                'destroy', 'crushing', 'winning', 'victory', 'perfect', 'amazing']

# Combine all keywords for detection
all_keywords = gaming_keywords + signature_keywords + crypto_keywords + challenge_keywords + hype_keywords

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Log user activity and get user object
        user = BotAnalytics.log_user_activity(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        msg = message.text.lower()
        matched_keywords = []
        response_category = None
        bot_responded = False
        
        # Check if any keywords are present
        for keyword in all_keywords:
            if keyword in msg:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            # Determine response category based on message content
            if any(word in msg for word in challenge_keywords):
                response_pool = challenge_responses + dismissive_responses
                response_category = "challenge_dismissive"
            elif any(word in msg for word in hype_keywords):
                response_pool = ultra_cocky_responses + dominant_responses
                response_category = "ultra_cocky_dominant"
            elif any(word in msg for word in crypto_keywords):
                response_pool = standard_responses + dominant_responses
                response_category = "crypto_focused"
            elif any(word in msg for word in signature_keywords):
                response_pool = ultra_cocky_responses + standard_responses
                response_category = "signature_ultra"
            else:
                response_pool = standard_responses + ultra_cocky_responses
                response_category = "standard_mixed"
            
            # Add some randomness - occasionally use different category
            if random.random() < 0.15:  # 15% chance for surprise response
                surprise_pool = dismissive_responses + dominant_responses
                response = random.choice(surprise_pool)
                response_category = "surprise_response"
            else:
                response = random.choice(response_pool)
            
            bot.reply_to(message, response)
            bot_responded = True
        
        # Log the message and response
        if user:
            BotAnalytics.log_message(
                user=user,
                message_text=message.text,
                message_type="text",
                response_category=response_category,
                keywords_matched=matched_keywords,
                bot_responded=bot_responded
            )
            
    except Exception as e:
        BotAnalytics.log_error("MESSAGE_HANDLER", str(e), context=f"Message: {message.text}")

# Flask app for uptime monitoring and analytics
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# Initialize database
print(f"DB URI: {os.getenv('SQLALCHEMY_DATABASE_URI')}")
db.init_app(app)

@app.route('/')
def home():
    try:
        with app.app_context():
            analytics = BotAnalytics.get_analytics_summary()
            
        uptime_hours = int((datetime.utcnow() - datetime(2025, 7, 27, 8, 0)).total_seconds() / 3600)
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎮 Dr Disrespect $DRD Bot - Champions Club Status</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); 
                    color: #fff; 
                    margin: 0; 
                    padding: 20px; 
                    min-height: 100vh;
                }
                .container { 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: rgba(255,255,255,0.1); 
                    border-radius: 15px; 
                    padding: 30px; 
                    backdrop-filter: blur(10px);
                }
                .status-online { color: #00ff00; font-weight: bold; }
                .status-box { 
                    background: rgba(255,255,255,0.05); 
                    border: 2px solid #ff6b35; 
                    border-radius: 10px; 
                    padding: 20px; 
                    margin: 20px 0; 
                }
                .stat-row { 
                    display: flex; 
                    justify-content: space-between; 
                    margin: 10px 0; 
                    padding: 5px 0; 
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
                .mustache { font-size: 1.5em; color: #ff6b35; }
                h1 { text-align: center; color: #ff6b35; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
                .arena-status { 
                    text-align: center; 
                    font-size: 1.2em; 
                    color: #ffff00; 
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎮 Dr Disrespect $DRD Bot Status</h1>
                <div class="arena-status">
                    <span class="mustache">🥸</span> The Two-Time is ONLINE and dominating! <span class="mustache">🥸</span>
                </div>
                
                <div class="status-box">
                    <h2>🏆 Champions Club Analytics</h2>
                    <div class="stat-row">
                        <span>Bot Status:</span>
                        <span class="status-online">ONLINE ✅</span>
                    </div>
                    <div class="stat-row">
                        <span>Total Champions:</span>
                        <span>{{ analytics.get('total_users', 'N/A') }}</span>
                    </div>
                    <div class="stat-row">
                        <span>Total Messages:</span>
                        <span>{{ analytics.get('total_messages', 'N/A') }}</span>
                    </div>
                    <div class="stat-row">
                        <span>Bot Responses:</span>
                        <span>{{ analytics.get('total_responses', 'N/A') }}</span>
                    </div>
                    <div class="stat-row">
                        <span>Response Rate:</span>
                        <span>{{ "%.1f"|format(analytics.get('response_rate', 0)) }}%</span>
                    </div>
                    <div class="stat-row">
                        <span>Arena Energy:</span>
                        <span style="color: #ff6b35;">MAXIMUM 🔥</span>
                    </div>
                    <div class="stat-row">
                        <span>Uptime:</span>
                        <span>{{ uptime_hours }} hours</span>
                    </div>
                </div>
                
                <div class="status-box">
                    <h3>⚔️ Violence. ⚡ Speed. 💣 Momentum.</h3>
                    <p><strong>$DRD Energy Status:</strong> MAXIMUM OVERDRIVE</p>
                    <p><strong>Champions Club Status:</strong> ACCEPTING NEW MEMBERS</p>
                    <p><strong>Arena Status:</strong> READY FOR DOMINATION</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #ccc;">
                    <p><em>The Arena awaits, champions. Back-to-back, two-time champion is ready!</em></p>
                    <p>🏆 Join the Champions Club on Telegram 🏆</p>
                </div>
            </div>
        </body>
        </html>
        """, analytics=analytics, uptime_hours=uptime_hours)
    except Exception as e:
        return f"""
        <h1>🎮 Dr Disrespect $DRD Bot Status</h1>
        <p>The Two-Time bot is running and ready to dominate the Champions Club!</p>
        <p>Status: <strong class="status-online">ONLINE</strong> ✅</p>
        <p>Violence. Speed. Momentum. $DRD Energy: <strong>MAXIMUM</strong> 🔥</p>
        <p><em>Analytics temporarily unavailable - The Arena awaits, champions.</em></p>
        """

@app.route('/status')
def status():
    try:
        with app.app_context():
            analytics = BotAnalytics.get_analytics_summary()
            
        return jsonify({
            "status": "online",
            "timestamp": datetime.utcnow().isoformat(),
            "bot": "Dr Disrespect $DRD Bot",
            "version": "2.0.0",
            "energy_level": "MAXIMUM",
            "arena_status": "READY FOR DOMINATION",
            "analytics": analytics
        })
    except Exception as e:
        return jsonify({
            "status": "online",
            "error": "Analytics unavailable",
            "bot": "Dr Disrespect $DRD Bot",
            "energy_level": "MAXIMUM",
            "arena_status": "READY FOR DOMINATION"
        })

@app.route('/health')
def health():
    """Health check endpoint for monitoring services"""
    try:
        # Quick database connectivity check
        with app.app_context():
            db.session.execute(db.text('SELECT 1')).fetchone()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "bot": "operational"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 500

@app.route('/analytics')
def analytics_endpoint():
    """Detailed analytics endpoint"""
    try:
        with app.app_context():
            analytics = BotAnalytics.get_analytics_summary()
            
            # Get recent activity
            recent_users = User.query.filter(
                User.last_activity >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # Get error count
            recent_errors = ErrorLog.query.filter(
                ErrorLog.created_at >= datetime.utcnow() - timedelta(days=7),
                ErrorLog.resolved == False
            ).count()
            
            return jsonify({
                "analytics": analytics,
                "recent_active_users": recent_users,
                "unresolved_errors": recent_errors,
                "timestamp": datetime.utcnow().isoformat()
            })
    except Exception as e:
        BotAnalytics.log_error("ANALYTICS_ENDPOINT", str(e))
        return jsonify({"error": "Analytics unavailable"}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram (if switching from polling)"""
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Invalid content type"}), 400
    except Exception as e:
        BotAnalytics.log_error("WEBHOOK", str(e))
        return jsonify({"error": "Webhook processing failed"}), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for external monitoring"""
    try:
        with app.app_context():
            total_users = User.query.count()
            active_users = User.query.filter(
                User.last_activity >= datetime.utcnow() - timedelta(days=1)
            ).count()
            
            today_messages = Message.query.filter(
                db.func.date(Message.created_at) == datetime.utcnow().date()
            ).count()
            
        return jsonify({
            "bot_status": "operational",
            "total_users": total_users,
            "active_users_24h": active_users,
            "messages_today": today_messages,
            "last_updated": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "bot_status": "operational", 
            "error": "Database stats unavailable"
        })

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# Main execution
if __name__ == "__main__":
    print("🎮 Dr Disrespect $DRD Bot v2.0 initializing...")
    print("⚔️ Violence. Speed. Momentum. Loading...")
    print("🏆 Champions Club energy: ACTIVATED")
    print("🔥 The Arena awaits domination!")
    
    # Initialize database tables
    with app.app_context():
        try:
            print("🗄️ Initializing Champions Club database...")
            db.create_all()
            print("✅ Database ready for domination!")
            
            # Log bot startup
            BotAnalytics.log_error("BOT_STARTUP", "Dr Disrespect Bot v2.0 started successfully", context="System startup")
            
        except Exception as e:
            print(f"⚠️ Database initialization error: {e}")
            print("   Bot will continue but analytics may be limited.")
    
    # Start Flask server for uptime monitoring
    keep_alive()
    
    print("🌐 Status page available at: http://0.0.0.0:5000")
    print("📊 Analytics dashboard: http://0.0.0.0:5000/analytics")
    print("💚 Health check: http://0.0.0.0:5000/health")
    print("🔗 API stats: http://0.0.0.0:5000/api/stats")
    print("🎯 Webhook ready: http://0.0.0.0:5000/webhook")
    
    # Start the bot with enhanced responses and error handling
    print("🚀 Bot is now LIVE and ready to dominate!")
try:
    bot.infinity_polling()
    except Exception as e:
        if "409" in str(e):
            print("⚠️  Another bot instance is running. Stopping this one.")
            print("   Wait a moment and try restarting if needed.")
        else:
            print(f"❌ Bot error: {e}")
            BotAnalytics.log_error("BOT_CRASH", str(e), context="Main polling loop")
            raise
