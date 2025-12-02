from pydantic import BaseModel

class UserMessage(BaseModel):
    user_id: str
    message: str
    channel: str

class PitchRequest(BaseModel):
    product_name: str
    is_green: bool
    consumption: int

class ChatResponse(BaseModel):
    reply: str | None = None
    state: str | None = None
    ui_data: dict | None = None
