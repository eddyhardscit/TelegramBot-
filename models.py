from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __bind_key__ = 'default'
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    username = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    total_messages = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    messages = db.relationship('Message', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.telegram_id}: {self.username or self.first_name}>'

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    telegram_message_id = db.Column(db.BigInteger, nullable=False)
    message_text = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(50), default='text')  # text, command, sticker, etc.
    response_category = db.Column(db.String(50), nullable=True)  # standard, ultra_cocky, dismissive, etc.
    keywords_matched = db.Column(db.Text, nullable=True)  # JSON string of matched keywords
    bot_responded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id}: {self.message_text[:50]}...>'

class BotStats(db.Model):
    __tablename__ = 'bot_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    total_messages = db.Column(db.Integer, default=0)
    total_responses = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    command_usage = db.Column(db.Text, nullable=True)  # JSON string
    keyword_stats = db.Column(db.Text, nullable=True)  # JSON string
    response_category_stats = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BotStats {self.date}: {self.total_messages} messages>'

class ErrorLog(db.Model):
    __tablename__ = 'error_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(100), nullable=False)
    error_message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    context = db.Column(db.Text, nullable=True)  # Additional context about the error
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ErrorLog {self.id}: {self.error_type}>'
