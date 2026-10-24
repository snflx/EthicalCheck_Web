import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, default))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


class Config:
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = _int_env("PORT", 5000, 1, 65535)
    FRONTEND_ORIGINS = [origin.strip() for origin in os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()]
    MAX_ANALYSES_PER_MINUTE = _int_env("MAX_ANALYSES_PER_MINUTE", 10, 1, 120)
    REQUEST_TIMEOUT_SECONDS = _int_env("REQUEST_TIMEOUT_SECONDS", 8, 2, 15)
    MAX_RESPONSE_BYTES = _int_env("MAX_RESPONSE_BYTES", 1_048_576, 16_384, 2_097_152)
