from pydantic import BaseModel


class ConfigModel(BaseModel):
    api_id: int
    api_hash: str
    phone: str
    chat_id: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    sender_filter: str | None = None


class SendCodeRequest(BaseModel):
    api_id: int
    api_hash: str
    phone: str


class VerifyCodeRequest(BaseModel):
    api_id: int
    api_hash: str
    phone: str
    code: str
    password: str | None = None


class FetchRequest(BaseModel):
    api_id: int
    api_hash: str
    chat_id: str
    date_from: str | None = None
    date_to: str | None = None
    sender_filter: str | None = None


class ExportRequest(BaseModel):
    api_id: int
    api_hash: str
    chat_id: str
    date_from: str | None = None
    date_to: str | None = None
    format: str = "excel"
