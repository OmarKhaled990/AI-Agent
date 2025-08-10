# backend/schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============ AUTHENTICATION ============

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    name: str
    role: str

# ============ ORGANIZATIONS ============

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    plan: str = Field(default="free")

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None

# ============ AGENTS/CHATBOTS ============

class AgentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    default_guidelines: str = Field(default="You are a helpful assistant.")
    system_prompt: Optional[str] = Field(default="You are a helpful AI assistant.")
    model: Optional[str] = Field(default="llama-3.1-8b-instant")
    temperature: Optional[float] = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000)

class ChatbotSettings(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)

class ChatbotResponse(BaseModel):
    id: int
    name: str
    status: str
    conversations: int
    messages: int
    created_at: Optional[datetime]

# ============ CHAT ============

class UserStart(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    session_id: Optional[str] = None

class ChatIn(BaseModel):
    text: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    email: Optional[str] = None
    user_id: Optional[int] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    message_id: Optional[int] = None

# ============ KNOWLEDGE BASE ============

class DocumentUpload(BaseModel):
    name: str
    content: Optional[str] = None
    file_type: str

class DocumentResponse(BaseModel):
    id: int
    name: str
    type: str
    size: int
    status: str
    uploaded_at: datetime

class KnowledgeBaseResponse(BaseModel):
    documents: List[DocumentResponse]

# ============ WIDGETS ============

class WidgetCreate(BaseModel):
    agent_id: int
    theme: str = Field(default="modern")
    primary_color: str = Field(default="#007bff")
    position: str = Field(default="bottom-right")
    welcome_message: Optional[str] = None

class WidgetUpdate(BaseModel):
    theme: Optional[str] = None
    primary_color: Optional[str] = None
    position: Optional[str] = None
    welcome_message: Optional[str] = None
    is_active: Optional[bool] = None

class WidgetConfig(BaseModel):
    agent_id: int
    title: str
    theme: str
    primary_color: str
    position: str
    welcome_message: str

# ============ API KEYS ============

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    permissions: List[str] = Field(default=["chat"])

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key: str  # Only returned on creation
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

# ============ ANALYTICS ============

class AnalyticsOverview(BaseModel):
    total_conversations: int
    total_messages: int
    avg_response_time: float
    user_satisfaction: float
    daily_stats: List[Dict[str, Any]]

class ConversationResponse(BaseModel):
    user_id: int
    user_name: str
    user_email: Optional[str]
    message_count: int
    last_message: datetime
    first_message: datetime

class MessageResponse(BaseModel):
    id: int
    direction: str
    text: str
    timestamp: datetime
    message_metadata: Optional[Dict[str, Any]] = None

# ============ INTEGRATIONS ============

class IntegrationCreate(BaseModel):
    integration_type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=128)
    config: Dict[str, Any] = Field(default={})

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

# ============ FEEDBACK ============

class FeedbackCreate(BaseModel):
    message_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

# ============ ADMIN ============

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class AdminOverview(BaseModel):
    agent: Dict[str, Any]
    users: List[Dict[str, Any]]
    total_conversations: int
    total_messages: int

# ============ BULK OPERATIONS ============

class BulkChatbotUpdate(BaseModel):
    chatbot_ids: List[int]
    updates: ChatbotSettings

class BulkDeleteRequest(BaseModel):
    ids: List[int]

# ============ WEBHOOKS ============

class WebhookCreate(BaseModel):
    url: str = Field(..., pattern=r'^https?://')
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = None

class WebhookUpdate(BaseModel):
    url: Optional[str] = Field(None, pattern=r'^https?://')
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None

# ============ CUSTOM FIELDS ============

class CustomFieldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    field_type: str = Field(..., pattern=r'^(text|number|boolean|select)$')
    options: Optional[List[str]] = None  # For select fields
    is_required: bool = Field(default=False)

class CustomFieldUpdate(BaseModel):
    name: Optional[str] = None
    options: Optional[List[str]] = None
    is_required: Optional[bool] = None

# ============ TEMPLATES ============

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    system_prompt: str
    default_guidelines: str
    model: str = Field(default="llama-3.1-8b-instant")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    tags: List[str] = Field(default=[])

class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    tags: List[str]
    created_at: datetime