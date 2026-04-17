import json
import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture(autouse=True)
def clean_config(tmp_path, monkeypatch):
    """ใช้ config file ชั่วคราวเพื่อไม่กระทบ config.json จริง"""
    import routers.fetch as fetch_router
    tmp_cfg = tmp_path / "config.json"
    monkeypatch.setattr(fetch_router, "CONFIG_FILE", tmp_cfg)
    yield tmp_cfg


@pytest.mark.asyncio
async def test_get_config_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/config")
    assert res.status_code == 200
    assert res.json() == {}


@pytest.mark.asyncio
async def test_save_and_load_config():
    payload = {
        "api_id": 39451198,
        "api_hash": "abc123",
        "phone": "+66812345678",
        "chat_id": "-100123456",
        "date_from": "2026-04-01",
        "date_to": "2026-04-10",
        "sender_filter": "@mybot",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        post_res = await client.post("/config", json=payload)
        assert post_res.status_code == 200
        assert post_res.json()["ok"] is True

        get_res = await client.get("/config")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["api_id"] == 39451198
        assert data["chat_id"] == "-100123456"
        assert data["sender_filter"] == "@mybot"


@pytest.mark.asyncio
async def test_save_config_missing_field():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/config", json={"api_id": 123})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_index_returns_html():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Telegram" in res.text
