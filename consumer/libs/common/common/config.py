import os
from pathlib import Path

CONSUMER_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = CONSUMER_ROOT / ".env"
SHARED_ENV = CONSUMER_ROOT.parent / "attacker" / ".env"
SHARED_KEYS = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD")


def _load(path: Path, keys: tuple[str, ...] | None = None) -> None:
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
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def load_env() -> None:
    _load(ENV_FILE)
    _load(SHARED_ENV, SHARED_KEYS)


def setting(name: str, default: str) -> str:
    load_env()
    return os.environ.get(name, default)


def database_url() -> str:
    load_env()
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "")
    host = os.environ.get("MYSQL_HOST", "127.0.0.1")
    port = os.environ.get("MYSQL_PORT", "3306")
    database = os.environ.get("MYSQL_DATABASE", "consumer_shop")
    from urllib.parse import quote_plus

    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}?charset=utf8mb4"
    )


def admin_database_url() -> str:
    return database_url().replace(
        f"/{setting('MYSQL_DATABASE', 'consumer_shop')}?",
        "/mysql?",
        1,
    )
