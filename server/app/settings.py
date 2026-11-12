import os
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
            continue
        key, value = trimmed.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def database_url() -> str:
    load_env()
    user = quote_plus(os.environ.get("MYSQL_USER", "root"))
    password = quote_plus(os.environ.get("MYSQL_PASSWORD", ""))
    host = os.environ.get("MYSQL_HOST", "127.0.0.1")
    port = os.environ.get("MYSQL_PORT", "3306")
    database = os.environ.get("MYSQL_DATABASE", "attack_console")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
