import datetime
import pytest
from unittest.mock import MagicMock
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from services.telegram import parse_date, parse_sender, detect_media, fmt_date


class TestParseDate:
    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_empty_returns_none(self):
        assert parse_date("") is None

    def test_valid_date(self):
        result = parse_date("2026-04-09")
        assert result == datetime.datetime(2026, 4, 9, tzinfo=datetime.timezone.utc)

    def test_end_of_day(self):
        result = parse_date("2026-04-09", end_of_day=True)
        assert result == datetime.datetime(2026, 4, 9, 23, 59, 59, tzinfo=datetime.timezone.utc)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_date("09/04/2026")


class TestParseSender:
    def _mock(self, **kwargs):
        m = MagicMock()
        for attr in ("username", "first_name", "title"):
            setattr(m, attr, kwargs.get(attr, None))
        return m

    def test_none_sender(self):
        assert parse_sender(None) == "unknown"

    def test_username(self):
        assert parse_sender(self._mock(username="johndoe")) == "@johndoe"

    def test_first_name_fallback(self):
        assert parse_sender(self._mock(first_name="John")) == "John"

    def test_title_fallback(self):
        assert parse_sender(self._mock(title="My Bot")) == "My Bot"

    def test_all_none(self):
        assert parse_sender(self._mock()) == "unknown"

    def test_username_takes_priority(self):
        assert parse_sender(self._mock(username="user", first_name="John")) == "@user"


class TestDetectMedia:
    def test_no_media(self):
        msg = MagicMock()
        msg.media = None
        assert detect_media(msg) == (None, False)

    def test_photo(self):
        msg = MagicMock()
        msg.media = MagicMock(spec=MessageMediaPhoto)
        media_type, is_image = detect_media(msg)
        assert media_type == "photo"
        assert is_image is True

    def test_image_document(self):
        msg = MagicMock()
        doc = MagicMock()
        doc.mime_type = "image/png"
        msg.media = MagicMock(spec=MessageMediaDocument)
        msg.media.document = doc
        media_type, is_image = detect_media(msg)
        assert media_type == "image"
        assert is_image is True

    def test_non_image_document(self):
        msg = MagicMock()
        doc = MagicMock()
        doc.mime_type = "application/pdf"
        msg.media = MagicMock(spec=MessageMediaDocument)
        msg.media.document = doc
        media_type, is_image = detect_media(msg)
        assert "pdf" in media_type
        assert is_image is False


class TestFmtDate:
    def test_adds_7_hours(self):
        utc = datetime.datetime(2026, 4, 9, 5, 0, 0, tzinfo=datetime.timezone.utc)
        assert fmt_date(utc) == "2026-04-09 12:00:00"

    def test_format_string(self):
        utc = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        assert fmt_date(utc) == "2026-01-01 07:00:00"
