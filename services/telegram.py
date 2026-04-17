import datetime
from fastapi import HTTPException
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# In-memory session store keyed by api_id
_sessions: dict[int, dict] = {}


def get_session(api_id: int, require_login: bool = True) -> dict:
    sess = _sessions.get(api_id)
    if not sess:
        raise HTTPException(status_code=401, detail="Session not found, send code first")
    if require_login and "session_string" not in sess:
        raise HTTPException(status_code=401, detail="ยังไม่ได้ login")
    return sess


async def ensure_connected(client: TelegramClient) -> None:
    if not client.is_connected():
        await client.connect()


def parse_date(s: str | None, end_of_day: bool = False) -> datetime.datetime | None:
    if not s:
        return None
    d = datetime.datetime.strptime(s, "%Y-%m-%d")
    if end_of_day:
        d = d.replace(hour=23, minute=59, second=59)
    return d.replace(tzinfo=datetime.timezone.utc)


def parse_sender(sender) -> str:
    if not sender:
        return "unknown"
    if hasattr(sender, "username") and sender.username:
        return f"@{sender.username}"
    if hasattr(sender, "first_name") and sender.first_name:
        return sender.first_name
    if hasattr(sender, "title") and sender.title:
        return sender.title
    return "unknown"


def detect_media(msg) -> tuple[str | None, bool]:
    """Returns (media_type, is_image)"""
    if not msg.media:
        return None, False
    if isinstance(msg.media, MessageMediaPhoto):
        return "photo", True
    if isinstance(msg.media, MessageMediaDocument):
        mime = getattr(msg.media.document, "mime_type", "") or ""
        if mime.startswith("image/"):
            return "image", True
        return f"document ({mime or 'unknown'})", False
    return "media", False


def fmt_date(dt: datetime.datetime) -> str:
    return (dt + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
