# Postgram — Telegram Group Posts Viewer

A web app for fetching and viewing the full post history from Telegram groups via the **MTProto API** (Telethon). Supports date range filtering, sender filtering, inline image display, and export to Excel or CSV.

> Unlike the standard Telegram Bot API which only retains updates for ~24 hours, MTProto API access via a user account retrieves the complete message history with no time limit.

---

## Features

- Fetch full message history from any group the account is a member of
- Filter by **date range** (calendar picker)
- Filter by **sender username or bot name** before fetching (reduces load time)
- Display attached **images inline** in the browser
- Export to **Excel (.xlsx)** with images embedded directly in cells
- Export to **CSV** with image URL column
- All settings (API credentials, chat ID, date range, sender filter) saved to a local `config.json` and auto-loaded on next launch
- Timestamps displayed in **Thailand time (UTC+7)**

---

## Requirements

- Python 3.10+
- Telegram **API ID** and **API Hash** — obtain from [my.telegram.org](https://my.telegram.org)
- A Telegram account that is a member of the target group

---

## Installation

```bash
git clone https://github.com/ninenox/postgram.git
cd postgram

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## Running

```bash
.venv/bin/uvicorn main:app --reload --port 8080
```

Open your browser at `http://127.0.0.1:8080`

---

## Usage

### Step 1 — Settings
- Enter your **API ID**, **API Hash**, and **phone number** (with country code, e.g. `+66812345678`)
- Enter the **Chat ID** (e.g. `-1001234567890`) or group **@username**
- Optionally set a **date range** and **sender filter**
- Click **💾 Save Config** to persist all settings for next time
- Click **Send OTP** to request a login code

### Step 2 — Verify OTP
- Enter the OTP received in the Telegram app
- If 2FA is enabled, also enter your password

### Step 3 — Fetch & Export
- Click **Fetch Posts** to retrieve messages matching your filters
- Click **📊 Export Excel** to download an `.xlsx` file with embedded images
- Click **📄 Export CSV** to download a `.csv` file with image URLs

> **Note:** You must click **Fetch Posts** before exporting, as export uses the cached result.

---

## Getting API ID and API Hash

1. Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number
2. Click **API Development Tools**
3. Fill in any app name and click **Create application**
4. Copy the `App api_id` (number) and `App api_hash` (string)

---

## Project Structure

```
postgram/
├── main.py                  # FastAPI app entry point
├── schemas.py               # Pydantic request/response models
├── services/
│   └── telegram.py          # Session store and Telethon helpers
├── routers/
│   ├── auth.py              # POST /auth/send-code, /auth/verify
│   ├── fetch.py             # GET+POST /config, POST /fetch, GET /media, GET /
│   └── export.py            # POST /export (Excel & CSV)
├── templates/
│   └── index.html           # Frontend UI
├── requirements.txt
└── config.json              # Local config (git-ignored)
```

---

## Excel Output Columns

| Column | Description |
|--------|-------------|
| Message ID | Telegram message ID |
| Date | Timestamp in Thailand time (UTC+7) |
| Sender | Username (`@name`) or display name |
| Text | Full message text |
| Image | Embedded image (photo or image document) |

---

## Tech Stack

| Library | Purpose |
|---------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework |
| [Telethon](https://docs.telethon.dev/) | Telegram MTProto client |
| [openpyxl](https://openpyxl.readthedocs.io/) | Excel file generation |
| [Pillow](https://python-pillow.org/) | Image resizing before embedding |
| [Jinja2](https://jinja.palletsprojects.com/) | HTML template rendering |
| [Flatpickr](https://flatpickr.js.org/) | Date picker UI (CDN) |
