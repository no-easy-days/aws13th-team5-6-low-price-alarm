import os

from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


MYSQL_HOST = _get_env("MYSQL_HOST")
MYSQL_PORT = int(_get_env("MYSQL_PORT"))
MYSQL_DATABASE = _get_env("MYSQL_DATABASE")
MYSQL_USER = _get_env("MYSQL_USER")
MYSQL_PASSWORD = _get_env("MYSQL_PASSWORD")

COLLECT_INTERVAL_SECONDS = int(os.getenv("COLLECT_INTERVAL_SECONDS", "60"))

UPBIT_TICKER_URL = "https://api.upbit.com/v1/ticker"
DEFAULT_COINS = [
    {"symbol": "BTC", "name": "Bitcoin"},
    {"symbol": "ETH", "name": "Ethereum"},
]

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/"
    f"{MYSQL_DATABASE}?charset=utf8mb4"
)
