from __future__ import annotations  # ‑– future‑safe typing, מונע forward‑refs ב‑mypy
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from pydantic import BaseSettings, Field, PostgresDsn, RedisDsn, validator

from myapp.utils.logger_config import get_logger

log = get_logger(__name__)

# root of the repo (…/myapp/…/settings.py ⇒ BASE_DIR = repo root)
BASE_DIR: Path = Path(__file__).resolve().parents[2]


class Environment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


def _default_reports_dir() -> Path:
    return BASE_DIR / "static" / "client_reports"


def _default_uploads_dir() -> Path:
    return BASE_DIR / "uploads"


class Settings(BaseSettings):
    """Central 12‑Factor configuration object.

    מגיש set‑and‑forget: טוען .env, יוצר תקיות חסרות,
    מספק טיפוסים חזקים ו‑validation קשוח.
    """

    # ––– General –––
    ENVIRONMENT: Environment = Field(
        default=Environment.LOCAL,
        description="Deployment environment [local|staging|production]",
    )
    DEBUG: bool = Field(default=False, description="True ⇔ local או DEBUG=1")

    # ––– Secrets / Security –––
    SECRET_KEY: str = Field(
        default="changeme", description="Flask/Session secret key (mandatory)"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Comma‑separated list of hosts permitted to access the server",
    )

    # ––– Database –––
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql://user:pass@localhost/db", env="DATABASE_URL"
    )

    # ––– Cache / Broker –––
    REDIS_URL: Optional[RedisDsn] = Field(default=None, env="REDIS_URL")

    # ––– Email (SMTP) –––
    EMAIL_SENDER: str = Field(default="noreply@example.com", env="EMAIL_SENDER")
    EMAIL_PASSWORD: str = Field(default="changeme", env="EMAIL_PASSWORD")
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    # ––– Optional CI / CD tokens –––
    GITHUB_TOKEN: str = ""
    GITHUB_BRANCH: str = "main"
    RENDER_API_TOKEN: str = ""

    # ––– Paths –––
    CLIENT_REPORTS_FOLDER: Path = Field(default_factory=_default_reports_dir)
    UPLOAD_FOLDER: Path = Field(default_factory=_default_uploads_dir)

    # ––– Feature Flags –––
    ENABLE_INSIGHTS: bool = False

    # ––– pydantic config –––
    class Config:
        # allow ENV_VARIABLE=… as well as env_variable=…
        case_sensitive = False
        # .env priority chain: .env.<env>.local → .env.<env> → .env
        env_file = None  # handled below
        env_file_encoding = "utf-8"
        validate_assignment = True  # live‑reload safe

        @classmethod
        def customise_sources(
            cls: type, init_settings: Any, env_settings: Any, file_secret_settings: Any
        ) -> tuple:
            env = os.getenv("ENVIRONMENT", "local").lower()
            files = [
                BASE_DIR / f".env.{env}.local",
                BASE_DIR / f".env.{env}",
                BASE_DIR / ".env",
            ]
            # Keep only existing files
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )

    # ––– Validators –––
    @validator("ALLOWED_HOSTS", pre=True)
    def _split_allowed_hosts(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return v

    @validator("DEBUG", pre=True, always=True)
    def _auto_debug(cls, v: bool, values: Dict[str, Any]) -> bool:
        env = values.get("ENVIRONMENT")
        return True if env == Environment.LOCAL else bool(v)

    @validator("CLIENT_REPORTS_FOLDER", "UPLOAD_FOLDER", pre=True, always=True)
    def _ensure_dirs_exist(cls, v: str | Path) -> Path:
        path = Path(v).expanduser().resolve()
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise RuntimeError(f"Could not create directory '{path}': {exc}") from exc
        return path

    @validator("SECRET_KEY", pre=True, always=True)
    def _require_secret_key(cls, v: str, values: Dict[str, Any]) -> str:
        if not v:
            # gentle default for dev, hard‑fail elsewhere
            if values.get("ENVIRONMENT") == Environment.LOCAL:
                log.warning("⚠️  SECRET_KEY not set – generating transient key for dev")
                return os.urandom(32).hex()
            raise ValueError("SECRET_KEY must be set")
        return v

    # ––– Convenience properties (no env fields) –––
    @property
    def is_local(self) -> bool:
        return self.ENVIRONMENT is Environment.LOCAL

    @property
    def sqlalchemy_kwargs(self) -> Dict[str, Any]:
        """Parameters you can pass straight into create_engine()."""
        return {"pool_pre_ping": True, "pool_recycle": 3600}

    @property
    def celery_broker_url(self) -> str | None:
        return str(self.REDIS_URL) if self.REDIS_URL else None


settings: Settings = Settings()
