from fastapi import APIRouter, Depends, HTTPException, WebSocket
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.orm import Session

import crud
import schemas
from database import SessionLocal

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_db():
    """요청 단위 DB 세션 생성/해제."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=schemas.AlertOut)
def create_alert(payload: schemas.AlertCreate, db: Session = Depends(get_db)):
    """알람 생성 (조건: GT/LT + 목표가)."""
    coin = crud.get_coin_by_id(db, payload.coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="coin not found")
    return crud.create_alert(db, payload.coin_id, payload.condition_type, payload.target_price)


@router.get("", response_model=schemas.AlertListOut)
def list_alerts(db: Session = Depends(get_db)):
    """전체 알람 목록."""
    items = crud.list_alerts(db)
    return schemas.AlertListOut(items=[schemas.AlertOut.model_validate(i) for i in items])


@router.websocket("/ws")
async def alerts_ws(websocket: WebSocket):
    """알람 트리거 이벤트를 받는 웹소켓."""
    manager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
