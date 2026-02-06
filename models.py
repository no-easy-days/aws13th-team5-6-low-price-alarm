from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import BIGINT, DECIMAL, DOUBLE, INTEGER
from sqlalchemy.orm import relationship

from database import Base


class Coin(Base):
    __tablename__ = "coins"
    __table_args__ = {"mysql_engine": "InnoDB"}

    # 코인 마스터
    id = Column(INTEGER, primary_key=True, index=True)
    market = Column(String(20), nullable=False, index=True)
    korean_name = Column(String(50), nullable=False)
    english_name = Column(String(100), nullable=False)

    history = relationship("CoinHistory", back_populates="coin")
    alerts = relationship("Alert", back_populates="coin")
    daily_stats = relationship("DailyCoinStatistics", back_populates="coin")


class CoinHistory(Base):
    __tablename__ = "coin_history"
    __table_args__ = {"mysql_engine": "InnoDB"}

    # 시계열 히스토리
    id = Column(BIGINT, primary_key=True, index=True)
    coin_id = Column(BIGINT, ForeignKey("coins.id"), nullable=False, index=True)
    trade_price = Column(DOUBLE, nullable=False)
    trade_volume = Column(DOUBLE, nullable=False)
    trade_timestamp = Column(INTEGER, nullable=False)
    opening_price = Column(DOUBLE, nullable=False)
    high_price = Column(DOUBLE, nullable=False)
    low_price = Column(DOUBLE, nullable=False)
    prev_closing_price = Column(DOUBLE, nullable=False)
    change_price = Column(DOUBLE, nullable=False)
    change_rate = Column(DOUBLE, nullable=False)
    collected_at = Column(DateTime, server_default=func.now(), nullable=True)

    coin = relationship("Coin", back_populates="history")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"mysql_engine": "InnoDB"}

    # 알람 조건/상태
    id = Column(BIGINT, primary_key=True, index=True)
    coin_id = Column(INTEGER, ForeignKey("coins.id"), nullable=False, index=True)
    condition_type = Column(String(2), nullable=False)
    target_price = Column(DECIMAL(10, 0), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    alerts_created_at = Column(DateTime, server_default=func.now(), nullable=False)
    alerts_triggered_at = Column(DateTime, nullable=True)

    coin = relationship("Coin", back_populates="alerts")


class DailyCoinStatistics(Base):
    __tablename__ = "daily_coin_statistics"
    __table_args__ = {"mysql_engine": "InnoDB"}

    # 일별 통계 (복합 PK: coin_id + date)
    coin_id = Column(BIGINT, ForeignKey("coins.id"), primary_key=True)
    statistics_date = Column(Date, primary_key=True)
    max_price = Column(DECIMAL(18, 2), nullable=True)
    min_price = Column(DECIMAL(18, 2), nullable=True)
    avg_price = Column(DECIMAL(18, 2), nullable=True)
    daily_statistics_created_at = Column(DateTime, server_default=func.now(), nullable=False)

    coin = relationship("Coin", back_populates="daily_stats")
