#!/usr/bin/env python3
"""
Dr Disrespect Bot Setup Script
Helps initialize the bot environment and database
"""

import os
import sys
from flask import Flask
from models import db

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not set")
        print("   Please set your PostgreSQL database URL")
        sys.exit(1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Initialize database
    db.init_app(app)
    return app

def setup_database():
    """Initialize database tables"""
    print("🗄️ Setting up Champions Club database...")
    
    app = create_app()
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Test connection
            result = db.session.execute(db.text('SELECT 1')).fetchone()
            if result:
                print("✅ Database connection test passed!")
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            sys.exit(1)

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    required_vars = ['TELEGRAM_BOT_TOKEN', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables before running the bot.")
        return False
    
    print("✅ All environment variables are set!")
    return True

def main():
    """Main setup function"""
    print("🎮 Dr Disrespect Bot Setup")
    print("⚔️ Violence. Speed. Momentum. Setting up the Champions Club!")
    print("-" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup database
    setup_database()
    
    print("-" * 60)
    print("🏆 Setup complete! The Arena is ready for domination!")
    print("🚀 Run 'python main.py' to start the bot")
    print("🌐 Monitor at: http://0.0.0.0:5000")

if __name__ == "__main__":
    main()