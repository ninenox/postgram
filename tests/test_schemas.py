import pytest
from pydantic import ValidationError

from schemas import (
    ConfigModel, SendCodeRequest, VerifyCodeRequest,
    FetchRequest, ExportRequest,
)


class TestConfigModel:
    def test_required_fields(self):
        cfg = ConfigModel(api_id=123, api_hash="abc", phone="+66812345678")
        assert cfg.api_id == 123
        assert cfg.chat_id is None
        assert cfg.sender_filter is None

    def test_optional_fields(self):
        cfg = ConfigModel(
            api_id=123, api_hash="abc", phone="+66",
            chat_id="-100123", date_from="2026-04-01",
            date_to="2026-04-10", sender_filter="@bot"
        )
        assert cfg.chat_id == "-100123"
        assert cfg.date_from == "2026-04-01"

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            ConfigModel(api_id=123, api_hash="abc")


class TestSendCodeRequest:
    def test_valid(self):
        req = SendCodeRequest(api_id=1, api_hash="hash", phone="+66")
        assert req.phone == "+66"

    def test_missing_phone_raises(self):
        with pytest.raises(ValidationError):
            SendCodeRequest(api_id=1, api_hash="hash")


class TestVerifyCodeRequest:
    def test_no_password(self):
        req = VerifyCodeRequest(api_id=1, api_hash="h", phone="+66", code="12345")
        assert req.password is None

    def test_with_password(self):
        req = VerifyCodeRequest(api_id=1, api_hash="h", phone="+66", code="12345", password="pw")
        assert req.password == "pw"


class TestFetchRequest:
    def test_defaults(self):
        req = FetchRequest(api_id=1, api_hash="h", chat_id="-100123")
        assert req.date_from is None
        assert req.sender_filter is None

    def test_with_filter(self):
        req = FetchRequest(api_id=1, api_hash="h", chat_id="-100", sender_filter="@mybot")
        assert req.sender_filter == "@mybot"


class TestExportRequest:
    def test_default_format(self):
        req = ExportRequest(api_id=1, api_hash="h", chat_id="-100")
        assert req.format == "excel"

    def test_csv_format(self):
        req = ExportRequest(api_id=1, api_hash="h", chat_id="-100", format="csv")
        assert req.format == "csv"
