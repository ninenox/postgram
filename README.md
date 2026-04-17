# Telegram Group Posts Viewer

A web app for fetching and viewing post history from Telegram groups via the MTProto API (Telethon), with date filtering and Excel/CSV export.

## Features

- Fetch full message history with no time limit
- Filter by date range
- Display attached images inline
- Export to **Excel (.xlsx)** with images embedded in cells
- Export to **CSV** with image URLs
- Auto-parse `roi_id` and `ocr` values from message text into separate columns
- Save API credentials to a local config file

## Requirements

- Python 3.10+
- Telegram API ID and API Hash from [my.telegram.org](https://my.telegram.org)

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
.venv/bin/uvicorn main:app --reload --port 8080
```

Open your browser at `http://127.0.0.1:8080`

### Steps

1. **Step 1** — Enter your API ID, API Hash, and phone number. Click **Save Config** to remember credentials, then click **Send OTP**.
2. **Step 2** — Enter the OTP received in Telegram.
3. **Step 3** — Enter the Chat ID or group username, select a date range, and click **Fetch Posts**.
4. Click **Export Excel** or **Export CSV** to download the data.

## Excel Output Columns

| Column | Description |
|--------|-------------|
| Message ID | Telegram message ID |
| Date | Timestamp in Thailand time (UTC+7) |
| Sender | Username or display name |
| Text | Full message text |
| ROI ID | Parsed `roi_id` value from text |
| OCR | Parsed numeric value from `ocr:` in text |
| Image | Embedded image attachment |

## Stack

- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [Telethon](https://docs.telethon.dev/) — Telegram MTProto client
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel export
- [Pillow](https://python-pillow.org/) — Image resizing
