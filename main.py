import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from routers import alerts, coins
from services.collector import start_collector, stop_collector
from services.ws import ConnectionManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 리소스 초기화 및 정리."""
    # 테이블 자동 생성(이미 있으면 변경 없음)
    Base.metadata.create_all(bind=engine)
    # 웹소켓 매니저/이벤트 루프를 앱 상태에 저장
    app.state.ws_manager = ConnectionManager()
    app.state.ws_loop = asyncio.get_running_loop()
    # 수집 스레드 시작
    start_collector(app)
    try:
        yield
    finally:
        # 수집 스레드 종료
        stop_collector(app)


app = FastAPI(title="Crypto Price Collector", lifespan=lifespan)

# 정적 파일(대시보드)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    """대시보드 HTML 제공."""
    return FileResponse("static/index.html")

# API 라우터 등록
app.include_router(coins.router)
app.include_router(alerts.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
