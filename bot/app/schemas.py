"""Pydantic request/response models for the public API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    lead_captured: bool = False


class LeadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=5, max_length=40)
    email: EmailStr
    service: str = Field(..., min_length=1, max_length=120)
    details: str = Field(..., min_length=1, max_length=4000)
    source: str = Field(default="website-form", max_length=40)


class LeadResponse(BaseModel):
    id: int
    ok: bool = True


class LeadRecord(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    service: str
    details: str
    source: str
    created_at: str


class HealthResponse(BaseModel):
    status: str
    telegram: bool
    smtp: bool
    model: Optional[str]
