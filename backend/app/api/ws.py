"""WebSocket 实时数据推送（模块4：WebSocket 实时数据推送）。

token 鉴权后，按 WS_PUSH_INTERVAL 周期推送行情/净值快照。
交易时段推送新浪秒级实时价（realtime_service），休市推送库中最新收盘。
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.services import realtime_service

router = APIRouter(tags=["实时推送"])


def _snapshot() -> dict:
    db = SessionLocal()
    try:
        return realtime_service.snapshot(db)
    finally:
        db.close()


@router.websocket("/ws/quotes")
async def ws_quotes(websocket: WebSocket) -> None:
    """实时行情推送。客户端连接时通过 query 参数 ?token=<jwt> 鉴权。"""
    token = websocket.query_params.get("token", "")
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=4401)
        return
    await websocket.accept()
    try:
        while True:
            snap = await asyncio.to_thread(_snapshot)
            await websocket.send_text(json.dumps(snap, ensure_ascii=False))
            await asyncio.sleep(settings.WS_PUSH_INTERVAL)
    except WebSocketDisconnect:
        return
    except Exception:  # noqa: BLE001 - 连接异常时安全关闭
        try:
            await websocket.close()
        except Exception:  # noqa: BLE001
            pass
