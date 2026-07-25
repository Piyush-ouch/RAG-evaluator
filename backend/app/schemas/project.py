"""
Organization & Project Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Organization
# ---------------------------------------------------------

class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    logo_url: str | None = None


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    plan: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------
# Project
# ---------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    chatbot_api_url: str | None = None
    chatbot_api_method: str = "POST"


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    chatbot_api_url: str | None = None
    chatbot_api_method: str | None = None
    chatbot_request_template: dict | None = None
    chatbot_response_path: str | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    chatbot_api_url: str | None = None
    chatbot_api_method: str
    org_id: uuid.UUID
    created_at: datetime | None = None
    settings: dict = {}

    model_config = {"from_attributes": True}


class ChatbotConfigRequest(BaseModel):
    """Configure the customer's chatbot API."""
    api_url: str
    api_key: str | None = None
    api_method: str = "POST"
    headers: dict | None = None
    request_template: dict | None = None
    response_path: str | None = None


class LLMConfigRequest(BaseModel):
    """Configure an LLM provider for a project."""
    name: str
    provider_type: str
    model_name: str
    api_key: str | None = None
    api_base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    is_judge: bool = False


class VectorDBConfigRequest(BaseModel):
    """Configure a vector database for a project."""
    name: str
    provider_type: str
    connection_config: dict = {}
    api_key: str | None = None
    collection_name: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = None


class ConnectionTestResponse(BaseModel):
    """Connection test result."""
    success: bool
    message: str
    latency_ms: float | None = None
