import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "common"))

from common.config import setting


def main() -> None:
    url = setting("ORDER_URL", "http://127.0.0.1:8094") + "/internal/recover"
    response = httpx.post(
        url,
        headers={"x-internal-token": setting("INTERNAL_TOKEN", "dev-internal-token")},
        timeout=20.0,
    )
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
