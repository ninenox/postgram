use actix_web::{get, post, web, App, HttpResponse, HttpServer, Responder};
use chrono::{DateTime, NaiveDate, TimeZone, Utc};
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct FetchRequest {
    token: String,
    chat_id: String,
    date_from: Option<String>,
    date_to: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TgUser {
    id: i64,
    first_name: Option<String>,
    username: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TgMessage {
    message_id: i64,
    date: i64,
    text: Option<String>,
    caption: Option<String>,
    from: Option<TgUser>,
    forward_from: Option<TgUser>,
    forward_date: Option<i64>,
}

#[derive(Serialize, Deserialize, Debug)]
struct TgUpdate {
    update_id: i64,
    message: Option<TgMessage>,
    channel_post: Option<TgMessage>,
}

#[derive(Serialize, Deserialize, Debug)]
struct TgResponse<T> {
    ok: bool,
    result: Option<T>,
    description: Option<String>,
}

#[derive(Serialize)]
struct PostItem {
    message_id: i64,
    date_utc: String,
    sender: String,
    text: String,
}

#[post("/fetch")]
async fn fetch_posts(req: web::Json<FetchRequest>) -> impl Responder {
    let client = Client::new();
    let mut all_messages: Vec<TgMessage> = Vec::new();
    let mut offset: i64 = 0;

    // Parse date filters
    let from_ts: Option<i64> = req.date_from.as_deref().and_then(|s| {
        NaiveDate::parse_from_str(s, "%Y-%m-%d")
            .ok()
            .map(|d| Utc.from_utc_datetime(&d.and_hms_opt(0, 0, 0).unwrap()).timestamp())
    });
    let to_ts: Option<i64> = req.date_to.as_deref().and_then(|s| {
        NaiveDate::parse_from_str(s, "%Y-%m-%d")
            .ok()
            .map(|d| Utc.from_utc_datetime(&d.and_hms_opt(23, 59, 59).unwrap()).timestamp())
    });

    loop {
        let url = format!(
            "https://api.telegram.org/bot{}/getUpdates?chat_id={}&offset={}&limit=100&allowed_updates=[\"message\",\"channel_post\"]",
            req.token, req.chat_id, offset
        );

        let resp = match client.get(&url).send().await {
            Ok(r) => r,
            Err(e) => return HttpResponse::BadGateway().json(serde_json::json!({"error": e.to_string()})),
        };

        let body: TgResponse<Vec<TgUpdate>> = match resp.json().await {
            Ok(b) => b,
            Err(e) => return HttpResponse::InternalServerError().json(serde_json::json!({"error": e.to_string()})),
        };

        if !body.ok {
            let msg = body.description.unwrap_or_else(|| "Telegram API error".into());
            return HttpResponse::BadRequest().json(serde_json::json!({"error": msg}));
        }

        let updates = match body.result {
            Some(u) => u,
            None => break,
        };

        if updates.is_empty() {
            break;
        }

        for upd in &updates {
            offset = upd.update_id + 1;
            let msg = upd.message.clone().or_else(|| upd.channel_post.clone());
            if let Some(m) = msg {
                // Only include messages from requested chat
                all_messages.push(m);
            }
        }

        if updates.len() < 100 {
            break;
        }
    }

    // Filter by date and build response
    let posts: Vec<PostItem> = all_messages
        .into_iter()
        .filter(|m| {
            if let Some(ft) = from_ts { if m.date < ft { return false; } }
            if let Some(tt) = to_ts { if m.date > tt { return false; } }
            true
        })
        .map(|m| {
            let dt: DateTime<Utc> = Utc.timestamp_opt(m.date, 0).unwrap();
            let sender = m.from
                .as_ref()
                .map(|u| u.username.clone().unwrap_or_else(|| u.first_name.clone().unwrap_or_default()))
                .unwrap_or_else(|| "channel".into());
            let text = m.text.or(m.caption).unwrap_or_else(|| "(no text)".into());
            PostItem {
                message_id: m.message_id,
                date_utc: dt.format("%Y-%m-%d %H:%M:%S UTC").to_string(),
                sender,
                text,
            }
        })
        .collect();

    HttpResponse::Ok().json(serde_json::json!({ "count": posts.len(), "posts": posts }))
}

#[get("/")]
async fn index() -> impl Responder {
    HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(HTML)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Server running at http://127.0.0.1:8080");
    HttpServer::new(|| {
        App::new()
            .service(index)
            .service(fetch_posts)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}

const HTML: &str = r#"<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Telegram Group Posts</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh;padding:24px}
  h1{color:#58a6ff;margin-bottom:24px;font-size:1.6rem}
  .card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:24px;max-width:700px;margin:0 auto 24px}
  label{display:block;font-size:.85rem;color:#8b949e;margin-bottom:4px;margin-top:14px}
  input{width:100%;padding:10px 12px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:.95rem;outline:none}
  input:focus{border-color:#58a6ff}
  .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  button{margin-top:20px;width:100%;padding:12px;background:#238636;border:none;border-radius:6px;color:#fff;font-size:1rem;cursor:pointer;font-weight:600;transition:background .2s}
  button:hover{background:#2ea043}
  button:disabled{background:#21262d;color:#8b949e;cursor:not-allowed}
  #status{margin-top:12px;font-size:.9rem;color:#8b949e;min-height:20px}
  #results{max-width:700px;margin:0 auto}
  .post{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin-bottom:12px}
  .post-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
  .sender{color:#58a6ff;font-weight:600;font-size:.9rem}
  .date{color:#8b949e;font-size:.8rem}
  .msg-id{color:#6e7681;font-size:.75rem}
  .text{line-height:1.6;white-space:pre-wrap;word-break:break-word}
  .count-badge{display:inline-block;background:#1f6feb;color:#fff;border-radius:20px;padding:4px 14px;font-size:.85rem;margin-bottom:16px}
  .empty{text-align:center;padding:40px;color:#8b949e}
</style>
</head>
<body>
<div class="card">
  <h1>📨 Telegram Group Posts</h1>
  <label>Bot Token</label>
  <input id="token" type="password" placeholder="1234567890:ABCDEFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"/>
  <label>Chat ID / Group ID</label>
  <input id="chat_id" placeholder="-1001234567890"/>
  <div class="row">
    <div>
      <label>วันที่เริ่มต้น (From)</label>
      <input id="date_from" type="date"/>
    </div>
    <div>
      <label>วันที่สิ้นสุด (To)</label>
      <input id="date_to" type="date"/>
    </div>
  </div>
  <button id="btn" onclick="fetchPosts()">ดึงข้อมูล</button>
  <div id="status"></div>
</div>
<div id="results"></div>

<script>
async function fetchPosts() {
  const token = document.getElementById('token').value.trim();
  const chat_id = document.getElementById('chat_id').value.trim();
  const date_from = document.getElementById('date_from').value || null;
  const date_to = document.getElementById('date_to').value || null;

  if (!token || !chat_id) {
    setStatus('⚠️ กรุณาใส่ Token และ Chat ID', '#f85149');
    return;
  }

  const btn = document.getElementById('btn');
  btn.disabled = true;
  setStatus('⏳ กำลังดึงข้อมูล...', '#8b949e');
  document.getElementById('results').innerHTML = '';

  try {
    const res = await fetch('/fetch', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ token, chat_id, date_from, date_to })
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus('❌ Error: ' + (data.error || 'Unknown error'), '#f85149');
      return;
    }

    setStatus(`✅ พบ ${data.count} โพสต์`, '#3fb950');
    renderPosts(data.posts);
  } catch(e) {
    setStatus('❌ ' + e.message, '#f85149');
  } finally {
    btn.disabled = false;
  }
}

function renderPosts(posts) {
  const el = document.getElementById('results');
  if (!posts || posts.length === 0) {
    el.innerHTML = '<div class="empty">ไม่พบโพสต์ในช่วงวันที่ที่เลือก</div>';
    return;
  }
  const badge = `<div class="count-badge">${posts.length} โพสต์</div>`;
  const items = posts.map(p => `
    <div class="post">
      <div class="post-header">
        <span class="sender">@${escHtml(p.sender)}</span>
        <span class="date">${escHtml(p.date_utc)}</span>
      </div>
      <div class="msg-id">Message ID: ${p.message_id}</div>
      <div class="text" style="margin-top:8px">${escHtml(p.text)}</div>
    </div>`).join('');
  el.innerHTML = badge + items;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function setStatus(msg, color) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.style.color = color;
}
</script>
</body>
</html>
"#;
