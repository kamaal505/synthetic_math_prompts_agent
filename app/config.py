import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # API Keys
    OPENAI_KEY: str = os.getenv("OPENAI_KEY", "")
    GEMINI_KEY: str = os.getenv("GEMINI_KEY", "")
    DEEPSEEK_KEY: str = os.getenv("DEEPSEEK_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database/math_agent.db")
    
    # App settings
    APP_NAME: str = "Synthetic Math Prompts API"
    APP_VERSION: str = "1.0.0"
    
    # Similarity settings
    SIMILARITY_THRESHOLD: float = 0.82
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Validation
    def validate(self):
        """Validate that required settings are present"""
        if not self.OPENAI_KEY:
            raise ValueError("OPENAI_KEY is required")
        if not self.GEMINI_KEY:
            raise ValueError("GEMINI_KEY is required")

# Create settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please check your .env file") 