import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("attendai.db")

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Cloud PostgreSQL (Render / Supabase / Neon) connection pooling
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

try:
    engine = create_engine(db_url, connect_args=connect_args, **engine_kwargs)
    # Test connection
    with engine.connect() as conn:
        pass
    masked_url = db_url.split("@")[-1] if "@" in db_url else db_url
    logger.info(f"Database connection verified: {masked_url}")
except Exception as e:
    if settings.is_production:
        logger.error(f"[CRITICAL] Could not connect to DATABASE_URL in production: {e}")
        raise RuntimeError(f"Database connection to PostgreSQL failed: {e}")
    else:
        logger.warning(f"Could not connect to {db_url}: {e}. Falling back to SQLite local database.")
        db_url = "sqlite:///./attendai.db"
        connect_args = {"check_same_thread": False}
        engine = create_engine(db_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
