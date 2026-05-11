from typing import Literal, List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation] = Field(default_factory=list)
    end_of_conversation: bool = False
