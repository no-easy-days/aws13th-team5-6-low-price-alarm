from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CoinCreate(BaseModel):
    """코인 생성 요청."""
    market: str = Field(..., max_length=20)
    korean_name: str = Field(..., max_length=50)
    english_name: str = Field(..., max_length=100)


class CoinOut(BaseModel):
    """코인 응답 DTO."""
    id: int
    market: str
    korean_name: str
    english_name: str

    model_config = {"from_attributes": True}


class PriceOut(BaseModel):
    """히스토리 차트용 가격 포인트."""
    trade_price: float
    collected_at: datetime

    model_config = {"from_attributes": True}


class HistoryOut(BaseModel):
    """히스토리 응답."""
    coin_id: int
    market: str
    items: List[PriceOut]


class AlertCreate(BaseModel):
    """알람 생성 요청."""
    coin_id: int
    condition_type: str
    target_price: float

    @field_validator("condition_type")
    @classmethod
    def validate_op(cls, value: str) -> str:
        allowed = {"GT", "LT"}
        if value not in allowed:
            raise ValueError("condition_type must be one of GT, LT")
        return value


class AlertOut(BaseModel):
    """알람 응답."""
    id: int
    coin_id: int
    condition_type: str
    target_price: float
    is_active: bool
    alerts_created_at: datetime
    alerts_triggered_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AlertListOut(BaseModel):
    """알람 목록 응답."""
    items: List[AlertOut]


class StatsOut(BaseModel):
    """일별 통계 단건."""
    coin_id: int
    date: date
    max: float
    min: float
    avg: float


class StatsListOut(BaseModel):
    """일별 통계 목록."""
    coin_id: int
    items: List[StatsOut]
