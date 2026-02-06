from datetime import date, datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import crud
import schemas
from database import SessionLocal

router = APIRouter(prefix="/coins", tags=["coins"])


def get_db():
    """요청 단위 DB 세션 생성/해제."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=schemas.CoinOut)
def create_coin(payload: schemas.CoinCreate, db: Session = Depends(get_db)):
    """코인 생성(시장 코드/이름). 이미 있으면 기존 값 반환."""
    exists = crud.get_coin_by_market(db, payload.market)
    if exists:
        return exists
    return crud.create_coin(
        db,
        payload.market,
        korean_name=payload.korean_name,
        english_name=payload.english_name,
    )


@router.get("", response_model=List[schemas.CoinOut])
def list_coins(db: Session = Depends(get_db)):
    """코인 목록 조회."""
    items = crud.list_coins(db)
    return [schemas.CoinOut.model_validate(item) for item in items]


@router.get("/{coin_id}/history", response_model=schemas.HistoryOut)
def get_history(
    coin_id: int,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    """기간 내 가격 히스토리 조회."""
    coin = crud.get_coin_by_id(db, coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="coin not found")

    from_dt = datetime.combine(from_date, time.min)
    to_dt = datetime.combine(to_date, time.max)
    items = crud.get_history(db, coin_id, from_dt, to_dt)

    return schemas.HistoryOut(
        coin_id=coin.id,
        market=coin.market,
        items=[schemas.PriceOut.model_validate(i) for i in items],
    )


@router.get("/{coin_id}/stats", response_model=schemas.StatsListOut)
def get_stats(
    coin_id: int,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    """기간 내 일별 통계 조회."""
    coin = crud.get_coin_by_id(db, coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="coin not found")

    from_dt = datetime.combine(from_date, time.min) if from_date else None
    to_dt = datetime.combine(to_date, time.max) if to_date else None
    rows = crud.get_daily_stats(db, coin_id, from_dt, to_dt)

    items = [
        schemas.StatsOut(
            coin_id=coin.id,
            date=row.statistics_date,
            max=float(row.max_price) if row.max_price is not None else 0.0,
            min=float(row.min_price) if row.min_price is not None else 0.0,
            avg=float(row.avg_price) if row.avg_price is not None else 0.0,
        )
        for row in rows
    ]

    return schemas.StatsListOut(coin_id=coin.id, items=items)
