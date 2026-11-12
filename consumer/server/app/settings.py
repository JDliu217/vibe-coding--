import os
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
SHARED_ENV = ROOT.parent / "attacker" / ".env"
SHARED_KEYS = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD")
DEFAULT_DATABASE = "consumer_shop"


def _load_file(path: Path, keys: tuple[str, ...] | None = None) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
            continue
        key, value = trimmed.split("=", 1)
        key = key.strip()
        if keys is not None and key not in keys:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_env() -> None:
    _load_file(ENV_FILE)
    _load_file(SHARED_ENV, SHARED_KEYS)


def mysql_parts() -> dict[str, str]:
    load_env()
    return {
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", ""),
        "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "port": os.environ.get("MYSQL_PORT", "3306"),
        "database": os.environ.get("MYSQL_DATABASE", DEFAULT_DATABASE),
    }


def _url(database: str) -> str:
    parts = mysql_parts()
    user = quote_plus(parts["user"])
    password = quote_plus(parts["password"])
    return (
        f"mysql+pymysql://{user}:{password}@{parts['host']}:{parts['port']}"
        f"/{database}?charset=utf8mb4"
    )


def database_url() -> str:
    return _url(mysql_parts()["database"])


def admin_url() -> str:
    return _url("mysql")
