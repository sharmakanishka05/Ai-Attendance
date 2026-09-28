import os
import json
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List, Union

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_models = os.path.join(BACKEND_DIR, "models") if os.path.isdir(os.path.join(BACKEND_DIR, "models")) else "./models"
_default_data = os.path.join(BACKEND_DIR, "data") if os.path.isdir(os.path.join(BACKEND_DIR, "data")) else "./data"

class Settings(BaseSettings):
    PROJECT_NAME: str = "KIT Kanpur Attendance Management"
    TAGLINE: str = "Kanpur Institute of Technology — Smart attendance, without the paperwork."
    API_V1_STR: str = "/api"
    APP_ENV: str = os.getenv("APP_ENV", "development")  # "development" or "production"
    
    SECRET_KEY: str = os.getenv("JWT_SECRET", "attendai_super_secret_production_key_2026_x89f")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database: Automatically normalize legacy postgres:// to postgresql://
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./attendai.db")

    # Computer Vision / Face Recognition Thresholds (Defaults)
    FACE_MATCH_THRESHOLD: float = float(os.getenv("FACE_MATCH_THRESHOLD", "0.70"))
    FACE_REVIEW_THRESHOLD: float = float(os.getenv("FACE_REVIEW_THRESHOLD", "0.52"))

    # File uploads & limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))
    DATA_DIR: str = os.getenv("DATA_DIR", _default_data)
    MODELS_DIR: str = os.getenv("MODELS_DIR", _default_models)

    # CORS: Allow comma-separated strings or list, strictly exclude wildcard '*' when allow_credentials=True
    CORS_ORIGINS: Union[str, List[str]] = "https://attendai-frontend.vercel.app,http://localhost:3000,http://127.0.0.1:3000"

    # Cookie settings
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "")  # "none", "lax", "strict", or empty (auto)
    COOKIE_SECURE: Union[str, bool] = os.getenv("COOKIE_SECURE", "")

    @model_validator(mode="after")
    def post_process_settings(self):
        # 1. Normalize postgres:// to postgresql:// (Render PostgreSQL connection string)
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

        # 2. Parse CORS_ORIGINS safely (supporting comma-separated string, JSON, or list)
        origins: List[str] = []
        raw = self.CORS_ORIGINS
        if isinstance(raw, list):
            raw_list = raw
        elif isinstance(raw, str):
            trimmed = raw.strip()
            if trimmed.startswith("[") and trimmed.endswith("]"):
                try:
                    raw_list = json.loads(trimmed)
                except Exception:
                    raw_list = [trimmed]
            else:
                raw_list = [o.strip() for o in trimmed.split(",") if o.strip()]
        else:
            raw_list = []

        for o in raw_list:
            cleaned = str(o).strip().rstrip("/")
            # Disallow wildcard origin because allow_credentials=True forbids '*'
            if cleaned and cleaned != "*":
                if cleaned not in origins:
                    origins.append(cleaned)

        # Ensure Vercel frontend is included by default
        default_allowed = [
            "https://attendai-frontend.vercel.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]
        for d in default_allowed:
            if d not in origins:
                origins.append(d)

        self.CORS_ORIGINS = origins
        return self

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def cookie_samesite_policy(self) -> str:
        if self.COOKIE_SAMESITE:
            return self.COOKIE_SAMESITE.lower()
        return "none" if self.is_production else "lax"

    @property
    def cookie_secure_policy(self) -> bool:
        if isinstance(self.COOKIE_SECURE, bool):
            return self.COOKIE_SECURE
        if isinstance(self.COOKIE_SECURE, str) and self.COOKIE_SECURE.strip():
            return self.COOKIE_SECURE.lower() in ("true", "1", "yes")
        return self.is_production

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "faces"), exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "reports"), exist_ok=True)
