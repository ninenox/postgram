from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import datetime, asyncio, json, pathlib

CONFIG_FILE = pathlib.Path("config.json")
app = FastAPI()

# In-memory store per api_id session
_sessions: dict[int, dict] = {}


class ConfigModel(BaseModel):
    api_id: int
    api_hash: str
    phone: str


@app.get("/config")
async def get_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


@app.post("/config")
async def save_config(cfg: ConfigModel):
    CONFIG_FILE.write_text(cfg.model_dump_json())
    return {"ok": True}


class SendCodeRequest(BaseModel):
    api_id: int
    api_hash: str
    phone: str


class VerifyCodeRequest(BaseModel):
    api_id: int
    api_hash: str
    phone: str
    code: str
    password: str | None = None  # 2FA password if enabled


class FetchRequest(BaseModel):
    api_id: int
    api_hash: str
    chat_id: str
    date_from: str | None = None
    date_to: str | None = None


def _parse_date(s: str | None, end_of_day=False) -> datetime.datetime | None:
    if not s:
        return None
    d = datetime.datetime.strptime(s, "%Y-%m-%d")
    if end_of_day:
        d = d.replace(hour=23, minute=59, second=59)
    return d.replace(tzinfo=datetime.timezone.utc)


@app.post("/auth/send-code")
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


@app.post("/auth/verify")
async def verify_code(req: VerifyCodeRequest):
    sess = _sessions.get(req.api_id)
    if not sess:
        raise HTTPException(status_code=400, detail="Session not found, send code first")

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


@app.post("/fetch")
async def fetch_messages(req: FetchRequest):
    sess = _sessions.get(req.api_id)
    if not sess or "session_string" not in sess:
        raise HTTPException(status_code=401, detail="ยังไม่ได้ login")

    client: TelegramClient = sess["client"]
    if not client.is_connected():
        await client.connect()

    date_from = _parse_date(req.date_from, end_of_day=False)
    date_to = _parse_date(req.date_to, end_of_day=True)

    try:
        entity = await client.get_entity(int(req.chat_id) if req.chat_id.lstrip("-").isdigit() else req.chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ไม่พบ chat: {e}")

    posts = []
    # ดึงจาก date_to ย้อนหลัง หยุดเมื่อถึง date_from (เร็วกว่า reverse=True มาก)
    async for msg in client.iter_messages(entity, limit=None, offset_date=date_to):
        if date_to and msg.date > date_to:
            continue
        if date_from and msg.date < date_from:
            break

        sender_name = "unknown"
        if msg.sender:
            s = msg.sender
            if hasattr(s, "username") and s.username:
                sender_name = f"@{s.username}"
            elif hasattr(s, "first_name"):
                sender_name = s.first_name or "unknown"
            elif hasattr(s, "title"):
                sender_name = s.title

        media_type = None
        if msg.media:
            if isinstance(msg.media, MessageMediaPhoto):
                media_type = "photo"
            elif isinstance(msg.media, MessageMediaDocument):
                media_type = "document"
            else:
                media_type = "media"

        posts.append({
            "message_id": msg.id,
            "date": msg.date.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "sender": sender_name,
            "text": msg.text or msg.message or "(no text)",
            "media": media_type,
        })

    posts.reverse()  # เรียงจากเก่าไปใหม่
    return {"count": len(posts), "posts": posts}


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Telegram Group Posts</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh;padding:24px}
  h1{color:#58a6ff;margin-bottom:6px;font-size:1.5rem}
  .sub{color:#8b949e;font-size:.85rem;margin-bottom:24px}
  .card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:24px;max-width:720px;margin:0 auto 20px}
  .card h2{font-size:1rem;color:#8b949e;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #21262d}
  label{display:block;font-size:.82rem;color:#8b949e;margin-bottom:4px;margin-top:12px}
  input{width:100%;padding:9px 12px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:.92rem;outline:none}
  input:focus{border-color:#58a6ff}
  .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .btn{margin-top:16px;width:100%;padding:11px;border:none;border-radius:6px;color:#fff;font-size:.95rem;cursor:pointer;font-weight:600;transition:background .2s}
  .btn-blue{background:#1f6feb}.btn-blue:hover{background:#388bfd}
  .btn-green{background:#238636}.btn-green:hover{background:#2ea043}
  .btn:disabled{background:#21262d;color:#6e7681;cursor:not-allowed}
  .status{margin-top:10px;font-size:.88rem;min-height:20px;padding:6px 0}
  .ok{color:#3fb950}.err{color:#f85149}.info{color:#8b949e}
  #step2,#step3{display:none}
  #results{max-width:720px;margin:0 auto}
  .post{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px;margin-bottom:10px}
  .post-header{display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:6px}
  .sender{color:#58a6ff;font-weight:600;font-size:.88rem}
  .date{color:#8b949e;font-size:.78rem}
  .mid{color:#6e7681;font-size:.73rem;margin-bottom:6px}
  .text{line-height:1.65;white-space:pre-wrap;word-break:break-word;font-size:.92rem}
  .media-badge{display:inline-block;background:#21262d;border-radius:4px;padding:2px 8px;font-size:.75rem;color:#8b949e;margin-top:6px}
  .count-badge{display:inline-block;background:#1f6feb;color:#fff;border-radius:20px;padding:4px 16px;font-size:.85rem;margin-bottom:14px}
  .empty{text-align:center;padding:40px;color:#8b949e}
  .hint{font-size:.78rem;color:#6e7681;margin-top:6px}
</style>
</head>
<body>
<div class="card">
  <h1>📨 Telegram Group Posts</h1>
  <p class="sub">ใช้ MTProto API (user account) ดึงประวัติโพสต์ได้ทั้งหมด</p>

  <!-- Step 1: Login -->
  <div id="step1">
    <h2>Step 1 — เข้าสู่ระบบ Telegram</h2>
    <label>API ID <span style="color:#6e7681">(จาก my.telegram.org)</span></label>
    <input id="api_id" type="text" placeholder="12345678"/>
    <label>API Hash</label>
    <input id="api_hash" type="password" placeholder="abcdef1234567890abcdef1234567890"/>
    <label>เบอร์โทรศัพท์ (พร้อม country code)</label>
    <input id="phone" type="text" placeholder="+66812345678"/>
    <p class="hint">⚠️ ต้องสมัคร API ID/Hash ที่ <a href="https://my.telegram.org" target="_blank" style="color:#58a6ff">my.telegram.org</a> ก่อน</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px">
      <button class="btn btn-blue" onclick="sendCode()">ส่ง OTP</button>
      <button class="btn" style="background:#30363d" onclick="saveConfig()">💾 บันทึก Config</button>
    </div>
    <div id="status1" class="status"></div>
  </div>

  <!-- Step 2: OTP -->
  <div id="step2">
    <h2>Step 2 — ยืนยัน OTP</h2>
    <label>รหัส OTP ที่ได้รับใน Telegram</label>
    <input id="otp" type="text" placeholder="12345" maxlength="10"/>
    <label>รหัส 2FA <span style="color:#6e7681">(ถ้าเปิดใช้งาน)</span></label>
    <input id="password2fa" type="password" placeholder="ไม่จำเป็นต้องกรอกถ้าไม่ได้เปิด 2FA"/>
    <button class="btn btn-blue" onclick="verifyCode()">ยืนยัน</button>
    <div id="status2" class="status"></div>
  </div>

  <!-- Step 3: Fetch -->
  <div id="step3">
    <h2>Step 3 — ดึงข้อมูล</h2>
    <label>Chat ID หรือ Username ของกลุ่ม</label>
    <input id="chat_id" placeholder="-4847957256 หรือ @groupname"/>
    <div class="row">
      <div>
        <label>วันที่เริ่มต้น ค.ศ.</label>
        <input id="date_from" type="date"/>
      </div>
      <div>
        <label>วันที่สิ้นสุด ค.ศ.</label>
        <input id="date_to" type="date"/>
      </div>
    </div>
    <button class="btn btn-green" onclick="fetchPosts()">ดึงโพสต์</button>
    <div id="status3" class="status"></div>
  </div>
</div>

<div id="results"></div>

<script>
let apiId = null, apiHash = null, phone = null;

function setStatus(id, msg, cls) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = 'status ' + cls;
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function loadConfig() {
  const res = await fetch('/config');
  if (!res.ok) return;
  const cfg = await res.json();
  if (cfg.api_id) document.getElementById('api_id').value = cfg.api_id;
  if (cfg.api_hash) document.getElementById('api_hash').value = cfg.api_hash;
  if (cfg.phone) document.getElementById('phone').value = cfg.phone;
  if (cfg.api_id) setStatus('status1', '✅ โหลด config สำเร็จ', 'ok');
}

async function saveConfig() {
  const api_id = parseInt(document.getElementById('api_id').value.trim());
  const api_hash = document.getElementById('api_hash').value.trim();
  const phone = document.getElementById('phone').value.trim();
  if (!api_id || !api_hash || !phone) { setStatus('status1','⚠️ กรอกข้อมูลให้ครบก่อนบันทึก','err'); return; }
  const res = await fetch('/config', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({api_id, api_hash, phone})
  });
  if (res.ok) setStatus('status1','💾 บันทึก config แล้ว','ok');
  else setStatus('status1','❌ บันทึกไม่สำเร็จ','err');
}

window.addEventListener('DOMContentLoaded', loadConfig);

async function sendCode() {
  apiId = parseInt(document.getElementById('api_id').value.trim());
  apiHash = document.getElementById('api_hash').value.trim();
  phone = document.getElementById('phone').value.trim();
  if (!apiId || !apiHash || !phone) { setStatus('status1','⚠️ กรอกข้อมูลให้ครบ','err'); return; }

  setStatus('status1','⏳ กำลังส่ง OTP...','info');
  const res = await fetch('/auth/send-code', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({api_id:apiId, api_hash:apiHash, phone})
  });
  const data = await res.json();
  if (!res.ok) { setStatus('status1','❌ '+data.detail,'err'); return; }
  setStatus('status1','','info');
  document.getElementById('step2').style.display = 'block';
  document.getElementById('step2').scrollIntoView({behavior:'smooth'});
  setStatus('status2','✅ ส่ง OTP แล้ว กรุณาตรวจสอบ Telegram','ok');
}

async function verifyCode() {
  const code = document.getElementById('otp').value.trim();
  const password = document.getElementById('password2fa').value.trim() || null;
  if (!code) { setStatus('status2','⚠️ กรอก OTP ก่อน','err'); return; }

  setStatus('status2','⏳ กำลังยืนยัน...','info');
  const res = await fetch('/auth/verify', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({api_id:apiId, api_hash:apiHash, phone, code, password})
  });
  const data = await res.json();
  if (!res.ok) { setStatus('status2','❌ '+data.detail,'err'); return; }
  setStatus('status2','✅ Login สำเร็จ!','ok');
  document.getElementById('step3').style.display = 'block';
  document.getElementById('step3').scrollIntoView({behavior:'smooth'});
}

async function fetchPosts() {
  const chat_id = document.getElementById('chat_id').value.trim();
  const date_from = document.getElementById('date_from').value || null;
  const date_to = document.getElementById('date_to').value || null;
  if (!chat_id) { setStatus('status3','⚠️ กรอก Chat ID ก่อน','err'); return; }

  setStatus('status3','⏳ กำลังดึงข้อมูล อาจใช้เวลาสักครู่...','info');
  document.getElementById('results').innerHTML = '';

  const res = await fetch('/fetch', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({api_id:apiId, api_hash:apiHash, chat_id, date_from, date_to})
  });
  const data = await res.json();
  if (!res.ok) { setStatus('status3','❌ '+data.detail,'err'); return; }

  setStatus('status3',`✅ พบ ${data.count} โพสต์`,'ok');
  renderPosts(data.posts);
}

function renderPosts(posts) {
  const el = document.getElementById('results');
  if (!posts.length) { el.innerHTML = '<div class="empty">ไม่พบโพสต์ในช่วงวันที่ที่เลือก</div>'; return; }
  const badge = `<div class="count-badge" style="margin-left:0">${posts.length} โพสต์</div>`;
  const items = posts.map(p => `
    <div class="post">
      <div class="post-header">
        <span class="sender">${esc(p.sender)}</span>
        <span class="date">${esc(p.date)}</span>
      </div>
      <div class="mid">Message ID: ${p.message_id}</div>
      <div class="text">${esc(p.text)}</div>
      ${p.media ? `<span class="media-badge">📎 ${p.media}</span>` : ''}
    </div>`).join('');
  el.innerHTML = badge + items;
}
</script>
</body>
</html>
"""
