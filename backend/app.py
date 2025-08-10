# backend/app.py
import os, secrets, json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import Optional, List
import jwt
import bcrypt
from pydantic import BaseModel
import aiofiles
import uuid
from fastapi import HTTPException, Depends, Header
from typing import Optional
import jwt

from db import SessionLocal
from models import (
    User, Agent, Guideline, Message, ConversationSummary, 
    Organization, APIKey, ChatbotWidget, AnalyticsEvent, 
    KnowledgeBase, Document
)
from schemas import (
    AgentCreate, UserStart, ChatIn, UserRegister, UserLogin,
    OrganizationCreate, APIKeyCreate, WidgetCreate, DocumentUpload,
    ChatbotSettings
)
from graph import run_agent_with_memory, summarize_history
from utils import process_document, generate_embeddings

load_dotenv()

app = FastAPI(
    title="AI Chatbot Platform",
    description="Professional AI chatbot platform with knowledge bases, analytics, and customization",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# debug_auth.py - Add this to your app.py to debug and fix the 401 issue

import logging
from fastapi import Request

# Add detailed logging to see what's happening
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests to see auth headers"""
    print(f"🌐 {request.method} {request.url.path}")
    
    # Log authorization header
    auth_header = request.headers.get("authorization")
    if auth_header:
        print(f"🔑 Auth header present: {auth_header[:20]}...")
    else:
        print("❌ No auth header found")
    
    # Log all headers for debugging
    print(f"📋 Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    print(f"📤 Response status: {response.status_code}")
    return response

# Updated verify_token with detailed debugging
def verify_token_debug(authorization: Optional[str] = Header(None)):
    """Debug version of token verification"""
    print(f"🔍 verify_token called with: {authorization}")
    
    if not authorization:
        print("❌ No authorization header provided")
        raise HTTPException(401, "Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        print(f"❌ Invalid auth format: {authorization}")
        raise HTTPException(401, "Invalid authorization header format")
    
    token = authorization.split(" ")[1]
    print(f"🎫 Extracted token: {token[:20]}...")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print(f"✅ Token decoded successfully: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        raise HTTPException(401, f"Invalid token: {str(e)}")

# Simple test endpoint without auth
@app.get("/api/test/no-auth")
def test_no_auth():
    """Test endpoint without authentication"""
    return {"message": "No auth required - working!"}

# Test endpoint with auth
@app.get("/api/test/with-auth")
def test_with_auth(user: User = Depends(get_current_user)):
    """Test endpoint with authentication"""
    return {"message": f"Auth working! User: {user.username}"}

# Alternative chatbots endpoint for testing
@app.get("/api/chatbots/debug")
def debug_chatbots(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Debug version of chatbots endpoint"""
    print(f"🔍 Debug chatbots called with auth: {authorization}")
    
    if not authorization:
        return {"error": "No authorization header", "code": "NO_AUTH_HEADER"}
    
    if not authorization.startswith("Bearer "):
        return {"error": "Invalid auth format", "format": authorization[:50]}
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found", "user_id": user_id}
        
        # Ensure user has organization
        if not user.organization_id:
            org = Organization(name=f"{user.username}'s Organization")
            db.add(org)
            db.flush()
            user.organization_id = org.id
            db.commit()
        
        chatbots = db.query(Agent).filter(Agent.organization_id == user.organization_id).all()
        
        return {
            "success": True,
            "user": {"id": user.id, "username": user.username},
            "organization_id": user.organization_id,
            "chatbots_count": len(chatbots),
            "chatbots": [{"id": c.id, "name": c.title} for c in chatbots]
        }
        
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError as e:
        return {"error": f"Invalid token: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# Check JWT secret is loaded
print(f"🔑 JWT_SECRET loaded: {JWT_SECRET[:10] if JWT_SECRET else 'NOT SET'}...")

# Override the original chatbots endpoint with debug version
@app.get("/api/chatbots")
def list_chatbots_with_debug(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Chatbots endpoint with detailed debugging"""
    print(f"🤖 Chatbots endpoint called")
    print(f"🔑 Auth header: {authorization}")
    
    if not authorization:
        print("❌ No auth header")
        raise HTTPException(401, "Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        print(f"❌ Wrong format: {authorization}")
        raise HTTPException(401, "Must start with 'Bearer '")
    
    token = authorization.split(" ")[1]
    print(f"🎫 Token: {token[:20]}...")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print(f"✅ Payload: {payload}")
        
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"❌ User {user_id} not found")
            raise HTTPException(404, "User not found")
        
        print(f"👤 User found: {user.username}")
        
        # Ensure organization
        if not user.organization_id:
            org = Organization(name=f"{user.username}'s Organization")
            db.add(org)
            db.flush()
            user.organization_id = org.id
            db.commit()
            print(f"🏢 Created organization: {org.id}")
        
        chatbots = db.query(Agent).filter(Agent.organization_id == user.organization_id).all()
        print(f"🤖 Found {len(chatbots)} chatbots")
        
        result = []
        for c in chatbots:
            result.append({
                "id": c.id,
                "name": c.title,
                "status": "active",
                "conversations": 0,
                "messages": 0,
                "created_at": datetime.utcnow().isoformat(),
                "model": getattr(c, 'model', 'llama-3.1-8b-instant'),
                "temperature": getattr(c, 'temperature', 0.3)
            })
        
        return result
        
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        raise HTTPException(401, f"Invalid token: {str(e)}")
    except Exception as e:
        print(f"🚨 Unexpected error: {e}")
        raise HTTPException(500, f"Server error: {str(e)}")

print("🔧 Debug auth endpoints added. Try /api/test/no-auth first, then /api/chatbots/debug")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

def get_current_user(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

# ============ AUTHENTICATION ============
def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header format")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# Fix the get_current_user function
def get_current_user(db: Session = Depends(get_db), payload: dict = Depends(verify_token)):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(401, "Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    return user

# Add a simple test endpoint to verify auth is working
@app.get("/api/auth/me")
def get_current_user_info(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "role": user.role
    }

# Fix the chatbots endpoint to ensure proper organization check
@app.get("/api/chatbots")
def list_chatbots(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # If user doesn't have an organization, create one
    if not user.organization_id:
        org = Organization(name=f"{user.username}'s Organization")
        db.add(org)
        db.flush()
        user.organization_id = org.id
        db.commit()
    
    chatbots = db.query(Agent).filter(Agent.organization_id == user.organization_id).all()
    
    return [{
        "id": c.id,
        "name": c.title,
        "status": "active",
        "conversations": db.query(func.count(func.distinct(Message.user_id))).filter(Message.agent_id == c.id).scalar() or 0,
        "messages": db.query(func.count(Message.id)).filter(Message.agent_id == c.id).scalar() or 0,
        "created_at": c.created_at.isoformat() if hasattr(c, 'created_at') else datetime.utcnow().isoformat(),
        "model": c.model or "llama-3.1-8b-instant",
        "temperature": c.temperature or 0.3
    } for c in chatbots]

@app.post("/api/auth/register")
def register(body: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(
        or_(User.email == body.email, User.username == body.username)
    ).first()
    if existing:
        raise HTTPException(400, "User already exists")
    
    # Hash password
    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt())
    
    # Create organization
    org = Organization(name=f"{body.username}'s Organization")
    db.add(org)
    db.flush()
    
    # Create user
    user = User(
        username=body.username,
        email=body.email,
        name=body.name,
        password_hash=hashed.decode(),
        organization_id=org.id,
        role="admin"
    )
    db.add(user)
    db.commit()
    
    # Generate token
    token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }, JWT_SECRET, algorithm="HS256")
    
    return {"token": token, "user": {"id": user.id, "username": user.username, "email": user.email}}

@app.post("/api/auth/login")
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
        raise HTTPException(401, "Invalid credentials")
    
    token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }, JWT_SECRET, algorithm="HS256")
    
    return {"token": token, "user": {"id": user.id, "username": user.username, "email": user.email}}

# ============ CHATBOTS ============

@app.get("/api/chatbots")
def list_chatbots(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chatbots = db.query(Agent).filter(Agent.organization_id == user.organization_id).all()
    return [{
        "id": c.id,
        "name": c.title,
        "status": "active",
        "conversations": db.query(func.count(func.distinct(Message.user_id))).filter(Message.agent_id == c.id).scalar(),
        "messages": db.query(func.count(Message.id)).filter(Message.agent_id == c.id).scalar(),
        "created_at": c.created_at.isoformat() if hasattr(c, 'created_at') else None
    } for c in chatbots]

@app.post("/api/chatbots")
def create_chatbot(body: AgentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = Agent(
        title=body.title,
        default_guidelines=body.default_guidelines,
        organization_id=user.organization_id,
        model=body.model or "llama-3.1-8b-instant",
        temperature=body.temperature or 0.3,
        max_tokens=body.max_tokens or 1000,
        system_prompt=body.system_prompt or "You are a helpful AI assistant."
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    # Create widget
    widget = ChatbotWidget(
        agent_id=agent.id,
        widget_id=str(uuid.uuid4()),
        theme="modern",
        primary_color="#007bff",
        position="bottom-right"
    )
    db.add(widget)
    db.commit()
    
    return {"id": agent.id, "widget_id": widget.widget_id}

@app.get("/api/chatbots/{chatbot_id}")
def get_chatbot(chatbot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chatbot = db.query(Agent).filter(
        Agent.id == chatbot_id,
        Agent.organization_id == user.organization_id
    ).first()
    if not chatbot:
        raise HTTPException(404, "Chatbot not found")
    
    widget = db.query(ChatbotWidget).filter(ChatbotWidget.agent_id == chatbot_id).first()
    
    return {
        "id": chatbot.id,
        "name": chatbot.title,
        "system_prompt": chatbot.system_prompt,
        "model": chatbot.model,
        "temperature": chatbot.temperature,
        "max_tokens": chatbot.max_tokens,
        "widget": {
            "widget_id": widget.widget_id if widget else None,
            "theme": widget.theme if widget else "modern",
            "primary_color": widget.primary_color if widget else "#007bff",
            "position": widget.position if widget else "bottom-right"
        }
    }

@app.put("/api/chatbots/{chatbot_id}")
def update_chatbot(chatbot_id: int, body: ChatbotSettings, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chatbot = db.query(Agent).filter(
        Agent.id == chatbot_id,
        Agent.organization_id == user.organization_id
    ).first()
    if not chatbot:
        raise HTTPException(404, "Chatbot not found")
    
    for field, value in body.dict(exclude_unset=True).items():
        if hasattr(chatbot, field):
            setattr(chatbot, field, value)
    
    db.commit()
    return {"success": True}

# ============ KNOWLEDGE BASE ============

@app.get("/api/chatbots/{chatbot_id}/knowledge")
def get_knowledge_base(chatbot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify ownership
    chatbot = db.query(Agent).filter(
        Agent.id == chatbot_id,
        Agent.organization_id == user.organization_id
    ).first()
    if not chatbot:
        raise HTTPException(404, "Chatbot not found")
    
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.agent_id == chatbot_id).first()
    if not kb:
        kb = KnowledgeBase(agent_id=chatbot_id)
        db.add(kb)
        db.commit()
        db.refresh(kb)
    
    documents = db.query(Document).filter(Document.knowledge_base_id == kb.id).all()
    
    return {
        "documents": [{
            "id": doc.id,
            "name": doc.name,
            "type": doc.file_type,
            "size": doc.file_size,
            "status": doc.status,
            "uploaded_at": doc.created_at.isoformat()
        } for doc in documents]
    }

@app.post("/api/chatbots/{chatbot_id}/knowledge/upload")
async def upload_document(
    chatbot_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify ownership
    chatbot = db.query(Agent).filter(
        Agent.id == chatbot_id,
        Agent.organization_id == user.organization_id
    ).first()
    if not chatbot:
        raise HTTPException(404, "Chatbot not found")
    
    # Check file type
    allowed_types = {".txt", ".pdf", ".docx", ".md", ".csv"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(400, "Unsupported file type")
    
    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Get or create knowledge base
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.agent_id == chatbot_id).first()
    if not kb:
        kb = KnowledgeBase(agent_id=chatbot_id)
        db.add(kb)
        db.flush()
    
    # Create document record
    document = Document(
        knowledge_base_id=kb.id,
        name=file.filename,
        file_path=file_path,
        file_type=file_ext,
        file_size=len(content),
        status="processing"
    )
    db.add(document)
    db.commit()
    
    # Process document in background
    if background_tasks:
        background_tasks.add_task(process_document_task, document.id)
    
    return {"document_id": document.id, "status": "uploaded"}

async def process_document_task(document_id: int):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            # Process and create embeddings
            await process_document(document, db)
            document.status = "completed"
            db.commit()
    except Exception as e:
        if document:
            document.status = "failed"
            db.commit()
    finally:
        db.close()

# ============ ANALYTICS ============

@app.get("/api/analytics/overview")
def analytics_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get all chatbots for this organization
    chatbot_ids = db.query(Agent.id).filter(Agent.organization_id == user.organization_id).all()
    chatbot_ids = [c[0] for c in chatbot_ids]
    
    if not chatbot_ids:
        return {
            "total_conversations": 0,
            "total_messages": 0,
            "avg_response_time": 0,
            "user_satisfaction": 0,
            "daily_stats": []
        }
    
    # Total conversations
    total_conversations = db.query(func.count(func.distinct(Message.user_id))).filter(
        Message.agent_id.in_(chatbot_ids)
    ).scalar()
    
    # Total messages
    total_messages = db.query(func.count(Message.id)).filter(
        Message.agent_id.in_(chatbot_ids)
    ).scalar()
    
    # Daily stats for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_stats = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        conversations = db.query(func.count(func.distinct(Message.user_id))).filter(
            Message.agent_id.in_(chatbot_ids),
            Message.ts >= date_start,
            Message.ts < date_end
        ).scalar()
        
        messages = db.query(func.count(Message.id)).filter(
            Message.agent_id.in_(chatbot_ids),
            Message.ts >= date_start,
            Message.ts < date_end
        ).scalar()
        
        daily_stats.append({
            "date": date.strftime("%Y-%m-%d"),
            "conversations": conversations,
            "messages": messages
        })
    
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "avg_response_time": 1.2,  # Mock data
        "user_satisfaction": 4.5,  # Mock data
        "daily_stats": daily_stats
    }

# ============ WIDGET & EMBED ============

@app.get("/api/widget/{widget_id}/config")
def get_widget_config(widget_id: str, db: Session = Depends(get_db)):
    widget = db.query(ChatbotWidget).filter(ChatbotWidget.widget_id == widget_id).first()
    if not widget:
        raise HTTPException(404, "Widget not found")
    
    agent = db.query(Agent).filter(Agent.id == widget.agent_id).first()
    
    return {
        "agent_id": agent.id,
        "title": agent.title,
        "theme": widget.theme,
        "primary_color": widget.primary_color,
        "position": widget.position,
        "welcome_message": widget.welcome_message or "Hello! How can I help you today?"
    }

# ============ PUBLIC CHAT API ============

@app.post("/api/widget/{widget_id}/chat")
def widget_chat(widget_id: str, body: ChatIn, db: Session = Depends(get_db)):
    widget = db.query(ChatbotWidget).filter(ChatbotWidget.widget_id == widget_id).first()
    if not widget:
        raise HTTPException(404, "Widget not found")
    
    agent = db.query(Agent).filter(Agent.id == widget.agent_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    # Find or create user session
    session_key = body.session_id or secrets.token_hex(12)
    user = db.query(User).filter(User.session_id == session_key).first()
    if not user:
        user = User(
            session_id=session_key,
            name="Anonymous",
            user_type="visitor"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Save incoming message
    db.add(Message(direction="in", user_id=user.id, agent_id=agent.id, text=body.text))
    db.commit()
    
    # Get conversation history
    recent = db.query(Message).filter(
        Message.user_id == user.id,
        Message.agent_id == agent.id
    ).order_by(desc(Message.id)).limit(20).all()
    recent = list(reversed(recent))
    
    history = [{"role": ("user" if m.direction == "in" else "assistant"), "content": m.text} for m in recent]
    
    # Get summary
    summary_row = db.query(ConversationSummary).filter(
        ConversationSummary.user_id == user.id,
        ConversationSummary.agent_id == agent.id
    ).first()
    long_summary = summary_row.summary if summary_row else ""
    
    # Generate response
    user_profile = {"name": user.name}
    reply = run_agent_with_memory(history, user_profile, agent.system_prompt, long_summary)
    
    # Save response
    db.add(Message(direction="out", user_id=user.id, agent_id=agent.id, text=reply))
    db.commit()
    
    # Update summary
    tail = history[-8:] + [{"role": "assistant", "content": reply}]
    new_summary = summarize_history(long_summary, tail)
    
    if summary_row:
        summary_row.summary = new_summary
    else:
        db.add(ConversationSummary(user_id=user.id, agent_id=agent.id, summary=new_summary))
    db.commit()
    
    return {"reply": reply, "session_id": session_key}

# ============ CONVERSATIONS ============

@app.get("/api/chatbots/{chatbot_id}/conversations")
def get_conversations(
    chatbot_id: int,
    page: int = 1,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify ownership
    chatbot = db.query(Agent).filter(
        Agent.id == chatbot_id,
        Agent.organization_id == user.organization_id
    ).first()
    if not chatbot:
        raise HTTPException(404, "Chatbot not found")
    
    # Get conversations (grouped by user)
    conversations = db.query(
        User.id,
        User.name,
        User.email,
        func.count(Message.id).label("message_count"),
        func.max(Message.ts).label("last_message"),
        func.min(Message.ts).label("first_message")
    ).join(Message).filter(
        Message.agent_id == chatbot_id
    ).group_by(User.id).order_by(
        desc(func.max(Message.ts))
    ).offset((page - 1) * limit).limit(limit).all()
    
    return [{
        "user_id": conv.id,
        "user_name": conv.name,
        "user_email": conv.email,
        "message_count": conv.message_count,
        "last_message": conv.last_message.isoformat(),
        "first_message": conv.first_message.isoformat()
    } for conv in conversations]

@app.get("/api/chatbots/{chatbot_id}/conversations/{user_id}/messages")
def get_conversation_messages(
    chatbot_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify ownership
    chatbot = db.query(Agent).filter(
        Agent.id == chatbot_id,
        Agent.organization_id == current_user.organization_id
    ).first()
    if not chatbot:
        raise HTTPException(404, "Chatbot not found")
    
    messages = db.query(Message).filter(
        Message.agent_id == chatbot_id,
        Message.user_id == user_id
    ).order_by(Message.ts).all()
    
    return [{
        "id": msg.id,
        "direction": msg.direction,
        "text": msg.text,
        "timestamp": msg.ts.isoformat(),
        "metadata": msg.message_metadata
    } for msg in messages]

# ============ LEGACY ENDPOINTS (for backward compatibility) ============
@app.post("/api/chat")
def chat_endpoint(body: ChatIn, db: Session = Depends(get_db)):
    """Main chat endpoint for authenticated users"""
    if not body.text:
        raise HTTPException(400, "text is required")

    # find user (by email or session)
    user = None
    if body.email:
        user = db.query(User).filter(User.email == body.email).first()
    if not user and body.session_id:
        user = db.query(User).filter(User.session_id == body.session_id).first()
    if not user:
        raise HTTPException(404, "Unknown session. Call /api/start first.")

    # ensure agent
    agent = db.query(Agent).first()
    if not agent:
        raise HTTPException(500, "No agent configured.")

    # guidelines precedence
    g_user = db.query(Guideline).filter(Guideline.agent_id == agent.id, Guideline.user_id == user.id).first()
    g_global = db.query(Guideline).filter(Guideline.agent_id == agent.id, Guideline.user_id.is_(None)).first()
    guidelines = (g_user.text if g_user else None) or (g_global.text if g_global else None) or agent.default_guidelines

    # save incoming msg first
    db.add(Message(direction="in", user_id=user.id, agent_id=agent.id, text=body.text))
    db.commit()

    # ---- SHORT-TERM: recent window ----
    WINDOW = 12
    recent = (
        db.query(Message)
          .filter(Message.user_id == user.id, Message.agent_id == agent.id)
          .order_by(desc(Message.id))
          .limit(WINDOW * 2)
          .all()
    )
    recent = list(reversed(recent))  # oldest -> newest
    history = [{"role": ("user" if m.direction == "in" else "assistant"), "content": m.text} for m in recent]

    # ---- LONG-TERM: summary ----
    summary_row = (
        db.query(ConversationSummary)
          .filter(ConversationSummary.user_id == user.id, ConversationSummary.agent_id == agent.id)
          .first()
    )
    long_summary = summary_row.summary if summary_row else ""

    # run agent with memory
    user_profile = {"name": user.name, "email": user.email}
    reply = run_agent_with_memory(history, user_profile, guidelines, long_summary)

    # save outgoing
    db.add(Message(direction="out", user_id=user.id, agent_id=agent.id, text=reply))
    db.commit()

    # update long-term summary using the latest tail
    tail = history[-8:] + [{"role":"assistant","content": reply}]
    new_summary = summarize_history(long_summary, tail)
    if summary_row:
        summary_row.summary = new_summary
    else:
        db.add(ConversationSummary(user_id=user.id, agent_id=agent.id, summary=new_summary))
    db.commit()

    return {"reply": reply}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/start")
def start_session(body: UserStart, db: Session = Depends(get_db)):
    # Legacy endpoint - create anonymous session
    user = User(
        session_id=body.session_id or secrets.token_hex(12),
        name=body.name or "Anonymous",
        email=body.email,
        user_type="visitor"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Get first agent
    agent = db.query(Agent).first()
    if not agent:
        agent = Agent(
            title="Default Agent",
            default_guidelines="You are a helpful assistant.",
            system_prompt="You are a helpful AI assistant."
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
    
    return {"session_id": user.session_id, "user_id": user.id, "agent_id": agent.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)