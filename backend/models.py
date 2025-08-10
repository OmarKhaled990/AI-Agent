# backend/models.py
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float, JSON
from datetime import datetime

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    plan = Column(String(64), default="free")  # free, pro, enterprise
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="organization")
    agents = relationship("Agent", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True, nullable=True)
    email = Column(String(256), unique=True, index=True, nullable=True)
    name = Column(String(128))
    session_id = Column(String(64), unique=True, index=True, nullable=True)
    password_hash = Column(String(256), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    role = Column(String(32), default="user")  # admin, user, viewer
    user_type = Column(String(32), default="registered")  # registered, visitor
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="users")
    messages = relationship("Message", back_populates="user")
    guidelines = relationship("Guideline", back_populates="user")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    default_guidelines = Column(Text, default="You are a helpful assistant.")
    system_prompt = Column(Text, default="You are a helpful AI assistant.")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    model = Column(String(64), default="llama-3.1-8b-instant")
    temperature = Column(Float, default=0.3)
    max_tokens = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="agents")
    messages = relationship("Message", back_populates="agent")
    guidelines = relationship("Guideline", back_populates="agent")
    knowledge_bases = relationship("KnowledgeBase", back_populates="agent")
    widgets = relationship("ChatbotWidget", back_populates="agent")

class Guideline(Base):
    __tablename__ = "guidelines"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="guidelines")
    agent = relationship("Agent", back_populates="guidelines")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    direction = Column(String(8), nullable=False)  # 'in' or 'out'
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    text = Column(Text)
    message_metadata = Column(JSON)  # Store additional data like response time, etc.
    ts = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="messages")
    agent = relationship("Agent", back_populates="messages")

class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    summary = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow)

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    key_hash = Column(String(256), nullable=False, unique=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatbotWidget(Base):
    __tablename__ = "chatbot_widgets"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    widget_id = Column(String(64), unique=True, index=True, nullable=False)
    theme = Column(String(32), default="modern")  # modern, classic, minimal
    primary_color = Column(String(7), default="#007bff")
    position = Column(String(32), default="bottom-right")  # bottom-right, bottom-left, etc.
    welcome_message = Column(Text)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON)  # Additional widget customization
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="widgets")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    name = Column(String(128), default="Knowledge Base")
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    name = Column(String(256), nullable=False)
    file_path = Column(String(512))
    file_type = Column(String(16))  # pdf, txt, docx, etc.
    file_size = Column(Integer)
    content = Column(Text)  # Extracted text content
    status = Column(String(32), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON)  # Store vector embeddings as JSON
    chunk_index = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(64), nullable=False)  # conversation_start, message_sent, etc.
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Integration(Base):
    __tablename__ = "integrations"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    integration_type = Column(String(64), nullable=False)  # slack, discord, website, etc.
    name = Column(String(128), nullable=False)
    config = Column(JSON)  # Store integration-specific configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rating = Column(Integer)  # 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)