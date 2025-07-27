import json
from datetime import datetime, date
from collections import defaultdict
from models import db, User, Message, BotStats, ErrorLog

class BotAnalytics:
    """Analytics system for tracking bot performance and user engagement"""
    
    @staticmethod
    def log_user_activity(telegram_id, username=None, first_name=None, last_name=None):
        """Log user activity and update user information"""
        try:
            user = User.query.filter_by(telegram_id=telegram_id).first()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                db.session.add(user)
            else:
                # Update user info if changed
                user.username = username or user.username
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                user.last_activity = datetime.utcnow()
                
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            BotAnalytics.log_error("USER_ACTIVITY", str(e))
            return None
    
    @staticmethod
    def log_message(user, message_text, message_type="text", response_category=None, keywords_matched=None, bot_responded=False):
        """Log incoming message and bot response"""
        try:
            # Update user message count
            user.total_messages += 1
            user.last_activity = datetime.utcnow()
            
            # Create message record
            message = Message(
                user_id=user.id,
                telegram_message_id=0,  # We don't always have this
                message_text=message_text,
                message_type=message_type,
                response_category=response_category,
                keywords_matched=json.dumps(keywords_matched) if keywords_matched else None,
                bot_responded=bot_responded
            )
            
            db.session.add(message)
            db.session.commit()
            
            # Update daily stats
            BotAnalytics.update_daily_stats()
            
        except Exception as e:
            db.session.rollback()
            BotAnalytics.log_error("MESSAGE_LOG", str(e))
    
    @staticmethod
    def update_daily_stats():
        """Update daily statistics"""
        try:
            today = date.today()
            stats = BotStats.query.filter_by(date=today).first()
            
            if not stats:
                stats = BotStats(date=today)
                db.session.add(stats)
            
            # Calculate today's stats
            today_messages = Message.query.filter(
                db.func.date(Message.created_at) == today
            ).count()
            
            today_responses = Message.query.filter(
                db.func.date(Message.created_at) == today,
                Message.bot_responded == True
            ).count()
            
            unique_users_today = db.session.query(Message.user_id).filter(
                db.func.date(Message.created_at) == today
            ).distinct().count()
            
            new_users_today = User.query.filter(
                db.func.date(User.created_at) == today
            ).count()
            
            # Update stats
            stats.total_messages = today_messages
            stats.total_responses = today_responses
            stats.unique_users = unique_users_today
            stats.new_users = new_users_today
            
            # Command usage stats
            command_stats = defaultdict(int)
            command_messages = Message.query.filter(
                db.func.date(Message.created_at) == today,
                Message.message_type == 'command'
            ).all()
            
            for msg in command_messages:
                if msg.message_text:
                    command = msg.message_text.split()[0]
                    command_stats[command] += 1
            
            stats.command_usage = json.dumps(dict(command_stats))
            
            # Response category stats
            category_stats = defaultdict(int)
            response_messages = Message.query.filter(
                db.func.date(Message.created_at) == today,
                Message.response_category.isnot(None)
            ).all()
            
            for msg in response_messages:
                if msg.response_category:
                    category_stats[msg.response_category] += 1
            
            stats.response_category_stats = json.dumps(dict(category_stats))
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            BotAnalytics.log_error("DAILY_STATS", str(e))
    
    @staticmethod
    def log_error(error_type, error_message, user_id=None, context=None):
        """Log application errors"""
        try:
            error_log = ErrorLog(
                error_type=error_type,
                error_message=error_message,
                user_id=user_id,
                context=context
            )
            db.session.add(error_log)
            db.session.commit()
        except Exception:
            # If we can't log to database, at least print it
            print(f"ERROR [{error_type}]: {error_message}")
    
    @staticmethod
    def get_analytics_summary():
        """Get comprehensive analytics summary"""
        try:
            # Overall stats
            total_users = User.query.count()
            total_messages = Message.query.count()
            total_responses = Message.query.filter(Message.bot_responded == True).count()
            
            # Recent activity (last 7 days)
            from datetime import timedelta
            week_ago = date.today() - timedelta(days=7)
            recent_stats = BotStats.query.filter(BotStats.date >= week_ago).all()
            
            # Top keywords
            recent_messages = Message.query.filter(
                Message.created_at >= datetime.utcnow() - timedelta(days=7),
                Message.keywords_matched.isnot(None)
            ).all()
            
            keyword_counts = defaultdict(int)
            for msg in recent_messages:
                if msg.keywords_matched:
                    try:
                        keywords = json.loads(msg.keywords_matched)
                        for keyword in keywords:
                            keyword_counts[keyword] += 1
                    except:
                        pass
            
            return {
                'total_users': total_users,
                'total_messages': total_messages,
                'total_responses': total_responses,
                'response_rate': (total_responses / total_messages * 100) if total_messages > 0 else 0,
                'recent_activity': len(recent_stats),
                'top_keywords': dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
        except Exception as e:
            BotAnalytics.log_error("ANALYTICS_SUMMARY", str(e))
            return {'error': 'Unable to generate analytics summary'}