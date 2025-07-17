from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL - default to BigQuery
DATABASE_URL = os.getenv("DATABASE_URL", "bigquery://turing-gpt.math_agent_dataset")

# Create engine based on database type
if DATABASE_URL.startswith("bigquery://"):
    # BigQuery configuration
    engine = create_engine(DATABASE_URL)
else:
    # SQLite configuration (for backward compatibility)
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 