from fastapi import APIRouter, HTTPException
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

from schemas import SendCodeRequest, VerifyCodeRequest
from services.telegram import _sessions, get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-code")
async def send_code(req: SendCodeRequest):
    client = TelegramClient(StringSession(), req.api_id, req.api_hash)
    await client.connect()
    try:
        result = await client.send_code_request(req.phone)
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=400, detail=str(e))

    _sessions[req.api_id] = {
        "client": client,
        "phone": req.phone,
        "phone_code_hash": result.phone_code_hash,
    }
    return {"ok": True, "message": "OTP sent"}


@router.post("/verify")
async def verify_code(req: VerifyCodeRequest):
    sess = get_session(req.api_id, require_login=False)
    client: TelegramClient = sess["client"]
    try:
        await client.sign_in(
            phone=req.phone,
            code=req.code,
            phone_code_hash=sess["phone_code_hash"],
        )
    except SessionPasswordNeededError:
        if not req.password:
            raise HTTPException(status_code=400, detail="2FA password required")
        await client.sign_in(password=req.password)
    except PhoneCodeInvalidError:
        raise HTTPException(status_code=400, detail="OTP ไม่ถูกต้อง")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    sess["session_string"] = client.session.save()
    return {"ok": True, "message": "Login สำเร็จ"}
