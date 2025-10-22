from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config.settings import Settings
 
settings = Settings()
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base() 