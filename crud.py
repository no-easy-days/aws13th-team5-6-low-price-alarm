from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

import models


def get_coin_by_id(db: Session, coin_id: int) -> Optional[models.Coin]:
    """코인 ID로 단건 조회."""
    return db.query(models.Coin).filter(models.Coin.id == coin_id).first()


def get_coin_by_market(db: Session, market: str) -> Optional[models.Coin]:
    """시장 코드로 단건 조회."""
    return db.query(models.Coin).filter(models.Coin.market == market).first()


def list_coins(db: Session) -> List[models.Coin]:
    """코인 전체 목록 조회."""
    return db.query(models.Coin).order_by(models.Coin.id.asc()).all()


def create_coin(
    db: Session,
    market: str,
    korean_name: str,
    english_name: str,
) -> models.Coin:
    """코인 생성."""
    coin = models.Coin(market=market, korean_name=korean_name, english_name=english_name)
    db.add(coin)
    db.commit()
    db.refresh(coin)
    return coin


def add_history(db: Session, coin_id: int, payload: dict) -> models.CoinHistory:
    """가격 히스토리 저장."""
    item = models.CoinHistory(coin_id=coin_id, **payload)
    db.add(item)
    db.commit()
    return item


def get_history(db: Session, coin_id: int, from_dt: datetime, to_dt: datetime) -> List[models.CoinHistory]:
    """기간 필터로 히스토리 조회."""
    return (
        db.query(models.CoinHistory)
        .filter(models.CoinHistory.coin_id == coin_id)
        .filter(models.CoinHistory.collected_at >= from_dt)
        .filter(models.CoinHistory.collected_at <= to_dt)
        .order_by(models.CoinHistory.collected_at.asc())
        .all()
    )


def create_alert(db: Session, coin_id: int, condition_type: str, target_price: float) -> models.Alert:
    """알람 생성."""
    alert = models.Alert(
        coin_id=coin_id,
        condition_type=condition_type,
        target_price=target_price,
        is_active=True,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts(db: Session) -> List[models.Alert]:
    """전체 알람 목록."""
    return db.query(models.Alert).order_by(models.Alert.id.asc()).all()


def list_active_alerts_by_coin(db: Session, coin_id: int) -> List[models.Alert]:
    """특정 코인의 활성 알람 목록."""
    return (
        db.query(models.Alert)
        .filter(models.Alert.coin_id == coin_id)
        .filter(models.Alert.is_active.is_(True))
        .order_by(models.Alert.id.asc())
        .all()
    )


def trigger_alert(db: Session, alert_id: int, triggered_at: datetime) -> Optional[models.Alert]:
    """알람 트리거 처리(비활성화 + 트리거 시각 기록)."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert or not alert.is_active:
        return None
    alert.is_active = False
    alert.alerts_triggered_at = triggered_at
    db.commit()
    db.refresh(alert)
    return alert


def get_daily_stats(db: Session, coin_id: int, from_dt: Optional[datetime], to_dt: Optional[datetime]):
    """일별 통계 조회."""
    query = (
        db.query(models.DailyCoinStatistics)
        .filter(models.DailyCoinStatistics.coin_id == coin_id)
        .order_by(models.DailyCoinStatistics.statistics_date.asc())
    )

    if from_dt:
        query = query.filter(models.DailyCoinStatistics.statistics_date >= from_dt.date())
    if to_dt:
        query = query.filter(models.DailyCoinStatistics.statistics_date <= to_dt.date())

    return query.all()


def refresh_daily_stats_for_date(db: Session, coin_id: int, stats_date: date) -> None:
    """특정 날짜의 일별 통계 upsert."""
    db.execute(
        text(
            """
            INSERT INTO daily_coin_statistics (
                coin_id,
                statistics_date,
                max_price,
                min_price,
                avg_price
            )
            SELECT
                coin_id,
                DATE(collected_at) AS statistics_date,
                MAX(trade_price) AS max_price,
                MIN(trade_price) AS min_price,
                AVG(trade_price) AS avg_price
            FROM coin_history
            WHERE coin_id = :coin_id
              AND DATE(collected_at) = :stats_date
            GROUP BY coin_id, DATE(collected_at)
            ON DUPLICATE KEY UPDATE
                max_price = VALUES(max_price),
                min_price = VALUES(min_price),
                avg_price = VALUES(avg_price)
            """
        ),
        {"coin_id": coin_id, "stats_date": stats_date},
    )
    db.commit()
