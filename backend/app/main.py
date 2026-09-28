import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import Base, engine, SessionLocal
from app.api import auth, students, classes, sessions, attendance, reports
from app.api import settings as settings_api

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("attendai")

app = FastAPI(
    title="AttendAI API",
    description="Smart attendance, without the paperwork. Production-grade AI attendance SaaS backend.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Mount routes
app.include_router(auth.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(classes.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")

@app.on_event("startup")
def startup_event():
    logger.info("Initializing AttendAI database tables and seeding realistic demo data...")
    db = SessionLocal()
    try:
        from app.seed import seed_database
        seed_database(db)
    except Exception as e:
        logger.error(f"Seeding error: {e}")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "product": "AttendAI",
        "tagline": "Smart attendance, without the paperwork.",
        "status": "operational",
        "env": settings.APP_ENV,
        "version": "1.0.0"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AttendAI API",
        "database": "connected",
        "env": settings.APP_ENV
    }
