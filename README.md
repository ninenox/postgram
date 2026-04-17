# Telegram Group Posts Viewer

เว็บแอปดึงและแสดงประวัติโพสต์จากกลุ่ม Telegram ผ่าน MTProto API (Telethon) พร้อม export เป็น Excel หรือ CSV

## Features

- ดึงประวัติโพสต์ย้อนหลังได้ทั้งหมด (ไม่จำกัดเวลา)
- Filter ตามช่วงวันที่
- แสดงรูปภาพที่แนบมาใน message
- Export เป็น **Excel (.xlsx)** พร้อมรูปภาพฝังใน cell
- Export เป็น **CSV** พร้อม URL รูปภาพ
- แยก column `roi_id` และ `ocr` จาก text อัตโนมัติ
- บันทึก API credentials ลง config file

## Requirements

- Python 3.10+
- Telegram API ID และ API Hash (สมัครที่ [my.telegram.org](https://my.telegram.org))

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
.venv/bin/uvicorn main:app --reload --port 8080
```

เปิดเบราว์เซอร์ที่ `http://127.0.0.1:8080`

### ขั้นตอนการใช้งาน

1. **Step 1** — กรอก API ID, API Hash และเบอร์โทรศัพท์ กด **บันทึก Config** เพื่อจำค่าไว้ใช้ครั้งต่อไป แล้วกด **ส่ง OTP**
2. **Step 2** — กรอก OTP ที่ได้รับใน Telegram
3. **Step 3** — กรอก Chat ID หรือ Username ของกลุ่ม เลือกช่วงวันที่ แล้วกด **ดึงโพสต์**
4. กด **Export Excel** หรือ **Export CSV** เพื่อดาวน์โหลดข้อมูล

## Excel Output Columns

| Column | Description |
|--------|-------------|
| Message ID | ID ของ message |
| Date | วันเวลา (เวลาไทย UTC+7) |
| Sender | ชื่อหรือ username ผู้ส่ง |
| Text | ข้อความเต็ม |
| ROI ID | ค่า `roi_id` ที่แยกจาก text |
| OCR | ค่าตัวเลขจาก `ocr:` ที่แยกจาก text |
| Image | รูปภาพที่แนบมา |

## Stack

- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [Telethon](https://docs.telethon.dev/) — Telegram MTProto client
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel export
- [Pillow](https://python-pillow.org/) — Image resizing
