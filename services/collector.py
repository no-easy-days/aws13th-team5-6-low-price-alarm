import asyncio
import logging
import threading
from datetime import datetime
from typing import Dict, Optional

import requests

import crud
import models
import schemas
from config import COLLECT_INTERVAL_SECONDS, DEFAULT_COINS, UPBIT_TICKER_URL
from database import SessionLocal

_ws_manager = None
_ws_loop: Optional[asyncio.AbstractEventLoop] = None
logger = logging.getLogger(__name__)


def _should_trigger(alert: models.Alert, trade_price: float) -> bool:
    """알람 조건(GT/LT)이 현재 가격을 만족하는지 판단."""
    target = float(alert.target_price)
    if alert.condition_type == "GT":
        return trade_price >= target
    if alert.condition_type == "LT":
        return trade_price <= target
    return False


def _broadcast_alert(payload: dict) -> None:
    """웹소켓으로 알람 트리거 이벤트 전파."""
    if not _ws_manager or not _ws_loop:
        return
    try:
        asyncio.run_coroutine_threadsafe(_ws_manager.broadcast_json(payload), _ws_loop)
    except Exception:
        pass


def set_ws_context(app) -> None:
    """FastAPI 앱 상태에 있는 웹소켓 매니저/루프를 주입."""
    global _ws_manager, _ws_loop
    _ws_manager = getattr(app.state, "ws_manager", None)
    _ws_loop = getattr(app.state, "ws_loop", None)


def ensure_default_coins():
    """기본 코인(BTC/ETH)이 없으면 초기 삽입."""
    db = SessionLocal()
    try:
        for item in DEFAULT_COINS:
            market = f"KRW-{item['symbol']}"
            exists = crud.get_coin_by_market(db, market)
            if not exists:
                crud.create_coin(
                    db,
                    market,
                    korean_name=item["symbol"],
                    english_name=item["name"],
                )
    finally:
        db.close()


def fetch_prices():
    """업비트 API에서 시세 수집 -> 히스토리 저장 -> 통계/알람 갱신."""
    db = SessionLocal()
    try:
        coins = crud.list_coins(db)
        if not coins:
            for item in DEFAULT_COINS:
                market = f"KRW-{item['symbol']}"
                crud.create_coin(
                    db,
                    market,
                    korean_name=item["symbol"],
                    english_name=item["name"],
                )
            coins = crud.list_coins(db)

        market_list = [c.market for c in coins]
        coin_map: Dict[str, models.Coin] = {c.market: c for c in coins}
        markets = ",".join(market_list)
        if not markets:
            return

        # 업비트 시세 조회
        response = requests.get(UPBIT_TICKER_URL, params={"markets": markets}, timeout=5)
        response.raise_for_status()
        data = response.json()

        updated_coin_ids = set()
        stats_date = datetime.utcnow().date()

        for item in data:
            market = item.get("market", "")
            coin = coin_map.get(market)
            if not coin:
                continue
            trade_timestamp = int(item.get("trade_timestamp", 0))
            if trade_timestamp > 2_147_483_647:
                trade_timestamp = trade_timestamp // 1000

            payload = {
                "trade_price": float(item.get("trade_price", 0)),
                "trade_volume": float(item.get("trade_volume", 0)),
                "trade_timestamp": trade_timestamp,
                "opening_price": float(item.get("opening_price", 0)),
                "high_price": float(item.get("high_price", 0)),
                "low_price": float(item.get("low_price", 0)),
                "prev_closing_price": float(item.get("prev_closing_price", 0)),
                "change_price": float(item.get("change_price", 0)),
                "change_rate": float(item.get("change_rate", 0)),
                "collected_at": datetime.utcnow(),
            }
            # 시세 히스토리 저장
            crud.add_history(db, coin.id, payload)
            updated_coin_ids.add(coin.id)

            trade_price = payload["trade_price"]
            alerts = crud.list_active_alerts_by_coin(db, coin.id)
            for alert in alerts:
                if _should_trigger(alert, trade_price):
                    triggered = crud.trigger_alert(db, alert.id, datetime.utcnow())
                    if triggered:
                        alert_out = schemas.AlertOut.model_validate(triggered).model_dump()
                        _broadcast_alert({"type": "alert_triggered", "alert": alert_out})

        # 하루 단위 통계 갱신
        for coin_id in updated_coin_ids:
            crud.refresh_daily_stats_for_date(db, coin_id, stats_date)
    finally:
        db.close()


def _collector_loop(stop_event: threading.Event, interval: int):
    """주기적 수집 루프(스레드)."""
    while not stop_event.is_set():
        try:
            fetch_prices()
        except Exception:
            logger.exception("Collector loop failed")
        stop_event.wait(interval)


def start_collector(app):
    """수집 스레드 시작 및 앱 상태에 핸들 보관."""
    ensure_default_coins()
    set_ws_context(app)
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_collector_loop,
        args=(stop_event, COLLECT_INTERVAL_SECONDS),
        daemon=True,
    )
    app.state.collector_stop_event = stop_event
    app.state.collector_thread = thread
    thread.start()


def stop_collector(app):
    """수집 스레드 종료."""
    stop_event = getattr(app.state, "collector_stop_event", None)
    thread = getattr(app.state, "collector_thread", None)
    if stop_event:
        stop_event.set()
    if thread:
        thread.join(timeout=5)

