import asyncio
from typing import Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # 현재 연결된 웹소켓 목록
        self._active: Set[WebSocket] = set()
        # 동시 접근 보호용 락
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """웹소켓 연결 승인 및 목록에 추가."""
        await websocket.accept()
        async with self._lock:
            self._active.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """웹소켓 연결 해제."""
        async with self._lock:
            self._active.discard(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        """모든 연결에 JSON 브로드캐스트."""
        async with self._lock:
            sockets = list(self._active)

        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                await self.disconnect(websocket)
