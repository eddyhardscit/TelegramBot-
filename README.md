# Dr Disrespect Bot ($DRD) - Enhanced Version 2.0

A high-performance Telegram bot that embodies the persona of Dr Disrespect with advanced analytics, database integration, and comprehensive monitoring capabilities.

## Features

### 🎮 Bot Capabilities
- **Multiple Response Categories**: Standard, ultra cocky, dismissive, dominant, and challenge responses
- **Smart Keyword Detection**: 40+ keywords across gaming, crypto, and signature term categories
- **Advanced Commands**: `/start`, `/drd`, `/arena`, `/club`, `/stats`
- **User Analytics**: Individual user statistics and activity tracking

### 📊 Analytics & Monitoring
- **Real-time Dashboard**: Professional web interface with Dr Disrespect theming
- **Database Integration**: PostgreSQL with user tracking, message logging, and statistics
- **Multiple Monitoring Endpoints**: `/health`, `/status`, `/analytics`, `/api/stats`
- **Error Logging**: Comprehensive error tracking and debugging

### 🚀 Production Ready
- **UptimeRobot Integration**: Health check endpoints for monitoring services
- **Webhook Support**: Ready for webhook deployment (currently uses polling)
- **Database Models**: Complete user, message, stats, and error logging models
- **Professional UI**: Responsive web dashboard with real-time statistics

## Files Structure

### Core Files
1. **main.py** - Main bot application with Flask server
2. **models.py** - Database models (User, Message, BotStats, ErrorLog)
3. **analytics.py** - Analytics system and tracking functions
4. **replit.md** - Project documentation and architecture

### Dependencies
- pyTelegramBotAPI==4.28.0
- flask==3.1.1
- flask-sqlalchemy==3.1.1
- psycopg2-binary==2.9.10
- python-dotenv==1.0.0

## Setup Instructions

### 1. Environment Variables
Set up these environment variables:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=postgresql://username:password@host:port/database
```

### 2. Installation
```bash
pip install pyTelegramBotAPI flask flask-sqlalchemy psycopg2-binary python-dotenv
```

### 3. Run the Bot
```bash
python main.py
```

## Monitoring URLs

### For UptimeRobot
- **Health Check**: `http://your-domain:5000/health` - Returns JSON health status
- **API Stats**: `http://your-domain:5000/api/stats` - Basic operational statistics
- **Status Endpoint**: `http://your-domain:5000/status` - Detailed bot status

### Web Dashboard
- **Main Dashboard**: `http://your-domain:5000/` - Full analytics dashboard
- **Analytics**: `http://your-domain:5000/analytics` - Detailed analytics JSON
- **Webhook**: `http://your-domain:5000/webhook` - Telegram webhook endpoint

## Bot Commands

- `/start` - Welcome message and command list
- `/drd` - Get random Dr Disrespect energy
- `/arena` - Enter competitive mode
- `/club` - Join the Champions Club
- `/stats` - View personal statistics

## Database Schema

### Users Table
- Telegram user information
- Activity tracking
- Message counts

### Messages Table
- All messages and responses
- Keyword matching logs
- Response categorization

### Bot Stats Table
- Daily statistics
- Command usage tracking
- Response analytics

### Error Logs Table
- Application error tracking
- Debugging information

## Response Categories

1. **Standard**: Classic Dr Disrespect energy with $DRD promotion
2. **Ultra Cocky**: Maximum confidence with elaborate boasts
3. **Dismissive**: For handling doubters and negative comments
4. **Dominant**: Pure power moves and authority
5. **Challenge**: For insults and confrontation

## Keyword Detection

- **Gaming**: doc, disrespect, arena, champions club, etc.
- **Signature**: violence, speed, momentum, mustache, etc.
- **Crypto**: drd, crypto, token, moon, diamond hands, etc.
- **Challenge**: better, suck, noob, trash, weak, etc.
- **Hype**: champion, legend, elite, pro, dominate, etc.

## Production Deployment

The bot is ready for production with:
- Comprehensive error handling
- Database connection pooling
- Health monitoring endpoints
- Professional web interface
- Analytics tracking
- User statistics

Perfect for UptimeRobot monitoring with multiple endpoint options for different monitoring needs.

---

**Violence. Speed. Momentum. The Champions Club awaits! 🏆**