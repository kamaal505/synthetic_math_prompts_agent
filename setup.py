#!/usr/bin/env python3
"""
Setup script for Enhanced Synthetic Math Prompts Agent
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    if not env_path.exists():
        env_content = """# API Keys
OPENAI_KEY=your_openai_api_key_here
GEMINI_KEY=your_gemini_api_key_here
DEEPSEEK_KEY=your_deepseek_api_key_here

# Database
DATABASE_URL=sqlite:///./database/math_agent.db

# Optional Settings
SIMILARITY_THRESHOLD=0.82
EMBEDDING_MODEL=text-embedding-3-small
"""
        with open(env_path, "w") as f:
            f.write(env_content)
        print("✅ Created .env file - please update with your API keys")
    else:
        print("✅ .env file already exists")

def create_database_dir():
    """Create database directory"""
    db_dir = Path("database")
    db_dir.mkdir(exist_ok=True)
    print("✅ Database directory created")

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import sqlalchemy
        import uvicorn
        print("✅ All required packages are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")

def main():
    print("🚀 Setting up Enhanced Synthetic Math Prompts Agent...")
    
    create_database_dir()
    create_env_file()
    check_dependencies()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Update .env file with your API keys")
    print("2. Run: uvicorn app.main:app --reload")
    print("3. Access API at: http://localhost:8000")
    print("4. View docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main() 