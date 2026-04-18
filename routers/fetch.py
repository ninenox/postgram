import json
import os
import pathlib

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from telethon.tl.types import MessageMediaDocument

from schemas import ConfigModel, FetchRequest
from services.telegram import (
    get_session, ensure_connected,
    parse_date, parse_sender, detect_media, fmt_date,
)

router = APIRouter(tags=["fetch"])
templates = Jinja2Templates(directory="templates")
CONFIG_FILE = pathlib.Path("config.json")


def _env_defaults() -> dict:
    raw_id = os.getenv("TG_API_ID")
    return {k: v for k, v in {
        "api_id":        int(raw_id) if raw_id and raw_id.isdigit() else None,
        "api_hash":      os.getenv("TG_API_HASH"),
        "phone":         os.getenv("TG_PHONE"),
        "chat_id":       os.getenv("TG_CHAT_ID"),
        "date_from":     os.getenv("TG_DATE_FROM"),
        "date_to":       os.getenv("TG_DATE_TO"),
        "sender_filter": os.getenv("TG_SENDER_FILTER"),
    }.items() if v is not None}


@router.get("/config")
async def get_config():
    cfg = _env_defaults()
    if CONFIG_FILE.exists():
        cfg.update(json.loads(CONFIG_FILE.read_text()))
    return cfg


@router.post("/config")
async def save_config(cfg: ConfigModel):
    CONFIG_FILE.write_text(cfg.model_dump_json())
    return {"ok": True}


@router.post("/fetch")
async def fetch_messages(req: FetchRequest):
    sess = get_session(req.api_id)
    client = sess["client"]
    await ensure_connected(client)

    date_from = parse_date(req.date_from)
    date_to = parse_date(req.date_to, end_of_day=True)

    try:
        entity = await client.get_entity(
            int(req.chat_id) if req.chat_id.lstrip("-").isdigit() else req.chat_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ไม่พบ chat: {e}")

    posts = []
    async for msg in client.iter_messages(entity, limit=None, offset_date=date_to):
        if date_to and msg.date > date_to:
            continue
        if date_from and msg.date < date_from:
            break

        sender_name = parse_sender(msg.sender)

        if req.sender_filter:
            keyword = req.sender_filter.lstrip("@").lower()
            if keyword not in sender_name.lstrip("@").lower():
                continue

        media_type, is_image = detect_media(msg)

        if is_image:
            sess.setdefault("messages", {})[f"{req.chat_id}:{msg.id}"] = msg

        posts.append({
            "message_id": msg.id,
            "date": fmt_date(msg.date),
            "sender": sender_name,
            "text": msg.text or msg.message or "(no text)",
            "media": media_type,
            "has_image": is_image,
        })

    posts.reverse()
    return {"count": len(posts), "posts": posts}


@router.get("/media/{api_id}/{chat_id}/{message_id}")
async def get_media(api_id: int, chat_id: str, message_id: int):
    sess = get_session(api_id)
    msg = sess.get("messages", {}).get(f"{chat_id}:{message_id}")
    if not msg:
        raise HTTPException(status_code=404, detail="ไม่พบรูปภาพ")

    client = sess["client"]
    await ensure_connected(client)

    data = await client.download_media(msg, file=bytes)
    if not data:
        raise HTTPException(status_code=404, detail="ดาวน์โหลดไม่สำเร็จ")

    mime = "image/jpeg"
    if isinstance(msg.media, MessageMediaDocument):
        mime = getattr(msg.media.document, "mime_type", "image/jpeg") or "image/jpeg"

    return Response(content=data, media_type=mime)


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
