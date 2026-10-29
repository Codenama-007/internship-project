from typing import Literal

from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    password: str


class OkOut(BaseModel):
    ok: bool = True


class MeOut(BaseModel):
    user: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatBody(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


class ChatOut(BaseModel):
    reply: str
