# backend/utils.py
import os
import json
import hashlib
import secrets
from typing import List, Dict, Any, Optional
import aiofiles
import asyncio
from datetime import datetime
import logging
from pathlib import Path

# Document processing imports
try:
    import PyPDF2
    import docx
    import pandas as pd
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError as e:
    logging.warning(f"Some optional dependencies not installed: {e}")

logger = logging.getLogger(__name__)

# Initialize embedding model (you may want to use a lighter model for production)
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.warning(f"Could not load embedding model: {e}")
    embedding_model = None

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"cb_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify an API key against its hash"""
    return hashlib.sha256(api_key.encode()).hexdigest() == api_key_hash

async def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text content from various file types"""
    try:
        if file_type == '.txt' or file_type == '.md':
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        
        elif file_type == '.pdf':
            return extract_pdf_text(file_path)
        
        elif file_type == '.docx':
            return extract_docx_text(file_path)
        
        elif file_type == '.csv':
            return extract_csv_text(file_path)
        
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return ""
    
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""

def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""

def extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {e}")
        return ""

def extract_csv_text(file_path: str) -> str:
    """Extract text from CSV file"""
    try:
        df = pd.read_csv(file_path)
        # Convert to a readable text format
        text = f"CSV Data with {len(df)} rows and {len(df.columns)} columns:\n"
        text += f"Columns: {', '.join(df.columns)}\n\n"
        
        # Add first few rows as sample
        sample_size = min(5, len(df))
        text += f"Sample data (first {sample_size} rows):\n"
        text += df.head(sample_size).to_string(index=False)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting CSV text: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundaries
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            for i in range(end, max(start + chunk_size - 200, start), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts"""
    if not embedding_model or not texts:
        return []
    
    try:
        embeddings = embedding_model.encode(texts)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return []

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0

async def process_document(document, db):
    """Process a document: extract text, create chunks, and generate embeddings"""
    from models import DocumentChunk
    
    try:
        # Extract text from file
        text_content = await extract_text_from_file(document.file_path, document.file_type)
        
        if not text_content:
            logger.warning(f"No text extracted from document {document.id}")
            return
        
        # Update document with extracted content
        document.content = text_content
        
        # Create chunks
        chunks = chunk_text(text_content)
        
        if not chunks:
            logger.warning(f"No chunks created from document {document.id}")
            return
        
        # Generate embeddings for chunks
        embeddings = generate_embeddings(chunks)
        
        # Save chunks to database
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = DocumentChunk(
                document_id=document.id,
                content=chunk_text,
                embedding=embedding,
                chunk_index=i
            )
            db.add(chunk)
        
        db.commit()
        logger.info(f"Processed document {document.id}: {len(chunks)} chunks created")
        
    except Exception as e:
        logger.error(f"Error processing document {document.id}: {e}")
        raise

def search_similar_chunks(query: str, chunks: List[Dict], limit: int = 5) -> List[Dict]:
    """Search for similar chunks using embeddings"""
    if not embedding_model or not chunks:
        return []
    
    try:
        # Generate embedding for query
        query_embedding = embedding_model.encode([query])[0].tolist()
        
        # Calculate similarities
        similarities = []
        for chunk in chunks:
            if 'embedding' in chunk and chunk['embedding']:
                similarity = cosine_similarity(query_embedding, chunk['embedding'])
                similarities.append((similarity, chunk))
        
        # Sort by similarity and return top results
        similarities.sort(reverse=True, key=lambda x: x[0])
        return [chunk for similarity, chunk in similarities[:limit]]
        
    except Exception as e:
        logger.error(f"Error searching similar chunks: {e}")
        return []

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s-.]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-.')

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def generate_widget_embed_code(widget_id: str, base_url: str = "http://localhost:3000") -> str:
    """Generate embeddable widget code"""
    return f"""
<!-- Chatbot Widget -->
<div id="chatbot-widget-{widget_id}"></div>
<script>
  (function() {{
    var script = document.createElement('script');
    script.src = '{base_url}/widget.js';
    script.onload = function() {{
      ChatbotWidget.init({{
        widgetId: '{widget_id}',
        apiUrl: '{base_url}/api/widget'
      }});
    }};
    document.head.appendChild(script);
  }})();
</script>
"""

def calculate_usage_stats(messages: List[Dict], days: int = 30) -> Dict[str, Any]:
    """Calculate usage statistics"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    recent_messages = [msg for msg in messages if msg.get('timestamp', datetime.min) > cutoff_date]
    
    total_messages = len(recent_messages)
    user_messages = len([msg for msg in recent_messages if msg.get('direction') == 'in'])
    bot_messages = len([msg for msg in recent_messages if msg.get('direction') == 'out'])
    
    # Calculate daily averages
    daily_avg = total_messages / days if days > 0 else 0
    
    return {
        'total_messages': total_messages,
        'user_messages': user_messages,
        'bot_messages': bot_messages,
        'daily_average': round(daily_avg, 2),
        'period_days': days
    }

def create_backup_data(db_session, organization_id: int) -> Dict[str, Any]:
    """Create backup data for an organization"""
    from models import Agent, User, Message, Document, KnowledgeBase
    
    try:
        # Get all data for organization
        agents = db_session.query(Agent).filter(Agent.organization_id == organization_id).all()
        users = db_session.query(User).filter(User.organization_id == organization_id).all()
        
        backup_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'organization_id': organization_id,
            'agents': [],
            'users': [],
            'conversations': []
        }
        
        # Backup agents
        for agent in agents:
            agent_data = {
                'id': agent.id,
                'title': agent.title,
                'description': agent.description,
                'system_prompt': agent.system_prompt,
                'model': agent.model,
                'temperature': agent.temperature,
                'max_tokens': agent.max_tokens
            }
            backup_data['agents'].append(agent_data)
            
            # Backup knowledge bases
            knowledge_bases = db_session.query(KnowledgeBase).filter(KnowledgeBase.agent_id == agent.id).all()
            agent_data['knowledge_bases'] = []
            
            for kb in knowledge_bases:
                kb_data = {
                    'id': kb.id,
                    'name': kb.name,
                    'description': kb.description,
                    'documents': []
                }
                
                documents = db_session.query(Document).filter(Document.knowledge_base_id == kb.id).all()
                for doc in documents:
                    kb_data['documents'].append({
                        'name': doc.name,
                        'content': doc.content,
                        'file_type': doc.file_type
                    })
                
                agent_data['knowledge_bases'].append(kb_data)
        
        # Backup users (anonymized)
        for user in users:
            if user.user_type == 'registered':  # Only backup registered users
                backup_data['users'].append({
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role
                })
        
        return backup_data
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return {}

def validate_widget_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize widget configuration"""
    valid_themes = ['modern', 'classic', 'minimal', 'dark']
    valid_positions = ['bottom-right', 'bottom-left', 'top-right', 'top-left']
    
    validated = {}
    
    # Theme validation
    if 'theme' in config and config['theme'] in valid_themes:
        validated['theme'] = config['theme']
    
    # Position validation
    if 'position' in config and config['position'] in valid_positions:
        validated['position'] = config['position']
    
    # Color validation (hex color)
    if 'primary_color' in config:
        color = config['primary_color']
        if isinstance(color, str) and len(color) == 7 and color.startswith('#'):
            try:
                int(color[1:], 16)  # Validate hex
                validated['primary_color'] = color
            except ValueError:
                pass
    
    # Welcome message validation
    if 'welcome_message' in config and isinstance(config['welcome_message'], str):
        message = config['welcome_message'][:500]  # Limit length
        validated['welcome_message'] = message
    
    return validated

async def cleanup_old_files(upload_dir: str, days_old: int = 30):
    """Clean up old uploaded files"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        upload_path = Path(upload_dir)
        
        if not upload_path.exists():
            return
        
        for file_path in upload_path.iterdir():
            if file_path.is_file():
                file_stat = file_path.stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {e}")
    
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")

def export_conversation_data(messages: List[Dict], format_type: str = 'json') -> str:
    """Export conversation data in various formats"""
    try:
        if format_type == 'json':
            return json.dumps(messages, indent=2, default=str)
        
        elif format_type == 'csv':
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Timestamp', 'Role', 'Message'])
            
            # Write data
            for msg in messages:
                writer.writerow([
                    msg.get('timestamp', ''),
                    msg.get('direction', ''),
                    msg.get('text', '')
                ])
            
            return output.getvalue()
        
        elif format_type == 'txt':
            text_output = "Conversation Export\n"
            text_output += "=" * 50 + "\n\n"
            
            for msg in messages:
                role = "User" if msg.get('direction') == 'in' else "Assistant"
                timestamp = msg.get('timestamp', '')
                text = msg.get('text', '')
                
                text_output += f"[{timestamp}] {role}: {text}\n\n"
            
            return text_output
        
        else:
            return json.dumps(messages, indent=2, default=str)
    
    except Exception as e:
        logger.error(f"Error exporting conversation data: {e}")
        return ""

def rate_limit_key(identifier: str, window_minutes: int = 60) -> str:
    """Generate rate limiting key"""
    import time
    window_start = int(time.time() // (window_minutes * 60))
    return f"rate_limit:{identifier}:{window_start}"

def mask_sensitive_data(data: str, mask_emails: bool = True, mask_phones: bool = True) -> str:
    """Mask sensitive data in text"""
    import re
    
    masked = data
    
    if mask_emails:
        # Mask email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        masked = re.sub(email_pattern, '[EMAIL_MASKED]', masked)
    
    if mask_phones:
        # Mask phone numbers (basic patterns)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # XXX-XXX-XXXX or similar
            r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',  # (XXX) XXX-XXXX
        ]
        for pattern in phone_patterns:
            masked = re.sub(pattern, '[PHONE_MASKED]', masked)
    
    return masked
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s-.]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-.')

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def generate_widget_embed_code(widget_id: str, base_url: str = "http://localhost:3000") -> str:
    """Generate embeddable widget code"""
    return f"""
<!-- Chatbot Widget -->
<div id="chatbot-widget-{widget_id}"></div>
<script>
  (function() {{
    var script = document.createElement('script');
    script.src = '{base_url}/widget.js';
    script.onload = function() {{
      ChatbotWidget.init({{
        widgetId: '{widget_id}',
        apiUrl: '{base_url}/api/widget'
      }});
    }};
    document.head.appendChild(script);
  }})();
</script>
"""

def calculate_usage_stats(messages: List[Dict], days: int = 30) -> Dict[str, Any]:
    """Calculate usage statistics"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    recent_messages = [msg for msg in messages if msg.get('timestamp', datetime.min) > cutoff_date]
    
    total_messages = len(recent_messages)
    user_messages = len([msg for msg in recent_messages if msg.get('direction') == 'in'])
    bot_messages = len([msg for msg in recent_messages if msg.get('direction') == 'out'])
    
    # Calculate daily averages
    daily_avg = total_messages / days if days > 0 else 0
    
    return {
        'total_messages': total_messages,
        'user_messages': user_messages,
        'bot_messages': bot_messages,
        'daily_average': round(daily_avg, 2),
        'period_days': days
    }

def create_backup_data(db_session, organization_id: int) -> Dict[str, Any]:
    """Create backup data for an organization"""
    from models import Agent, User, Message, Document, KnowledgeBase
    
    try:
        # Get all data for organization
        agents = db_session.query(Agent).filter(Agent.organization_id == organization_id).all()
        users = db_session.query(User).filter(User.organization_id == organization_id).all()
        
        backup_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'organization_id': organization_id,
            'agents': [],
            'users': [],
            'conversations': []
        }
        
        # Backup agents
        for agent in agents:
            agent_data = {
                'id': agent.id,
                'title': agent.title,
                'description': agent.description,
                'system_prompt': agent.system_prompt,
                'model': agent.model,
                'temperature': agent.temperature,
                'max_tokens': agent.max_tokens
            }
            backup_data['agents'].append(agent_data)
            
            # Backup knowledge bases
            knowledge_bases = db_session.query(KnowledgeBase).filter(KnowledgeBase.agent_id == agent.id).all()
            agent_data['knowledge_bases'] = []
            
            for kb in knowledge_bases:
                kb_data = {
                    'id': kb.id,
                    'name': kb.name,
                    'description': kb.description,
                    'documents': []
                }
                
                documents = db_session.query(Document).filter(Document.knowledge_base_id == kb.id).all()
                for doc in documents:
                    kb_data['documents'].append({
                        'name': doc.name,
                        'content': doc.content,
                        'file_type': doc.file_type
                    })
                
                agent_data['knowledge_bases'].append(kb_data)
        
        # Backup users (anonymized)
        for user in users:
            if user.user_type == 'registered':  # Only backup registered users
                backup_data['users'].append({
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role
                })
        
        return backup_data
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return {}

def validate_widget_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize widget configuration"""
    valid_themes = ['modern', 'classic', 'minimal', 'dark']
    valid_positions = ['bottom-right', 'bottom-left', 'top-right', 'top-left']
    
    validated = {}
    
    # Theme validation
    if 'theme' in config and config['theme'] in valid_themes:
        validated['theme'] = config['theme']
    
    # Position validation
    if 'position' in config and config['position'] in valid_positions:
        validated['position'] = config['position']
    
    # Color validation (hex color)
    if 'primary_color' in config:
        color = config['primary_color']
        if isinstance(color, str) and len(color) == 7 and color.startswith('#'):
            try:
                int(color[1:], 16)  # Validate hex
                validated['primary_color'] = color
            except ValueError:
                pass
    
    # Welcome message validation
    if 'welcome_message' in config and isinstance(config['welcome_message'], str):
        message = config['welcome_message'][:500]  # Limit length
        validated['welcome_message'] = message
    
    return validated

async def cleanup_old_files(upload_dir: str, days_old: int = 30):
    """Clean up old uploaded files"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        upload_path = Path(upload_dir)
        
        if not upload_path.exists():
            return
        
        for file_path in upload_path.iterdir():
            if file_path.is_file():
                file_stat = file_path.stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {e}")
    
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")

def export_conversation_data(messages: List[Dict], format_type: str = 'json') -> str:
    """Export conversation data in various formats"""
    try:
        if format_type == 'json':
            return json.dumps(messages, indent=2, default=str)
        
        elif format_type == 'csv':
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Timestamp', 'Role', 'Message'])
            
            # Write data
            for msg in messages:
                writer.writerow([
                    msg.get('timestamp', ''),
                    msg.get('direction', ''),
                    msg.get('text', '')
                ])
            
            return output.getvalue()
        
        elif format_type == 'txt':
            text_output = "Conversation Export\n"
            text_output += "=" * 50 + "\n\n"
            
            for msg in messages:
                role = "User" if msg.get('direction') == 'in' else "Assistant"
                timestamp = msg.get('timestamp', '')
                text = msg.get('text', '')
                
                text_output += f"[{timestamp}] {role}: {text}\n\n"
            
            return text_output
        
        else:
            return json.dumps(messages, indent=2, default=str)
    
    except Exception as e:
        logger.error(f"Error exporting conversation data: {e}")
        return ""

def rate_limit_key(identifier: str, window_minutes: int = 60) -> str:
    """Generate rate limiting key"""
    import time
    window_start = int(time.time() // (window_minutes * 60))
    return f"rate_limit:{identifier}:{window_start}"

def mask_sensitive_data(data: str, mask_emails: bool = True, mask_phones: bool = True) -> str:
    """Mask sensitive data in text"""
    import re
    
    masked = data
    
    if mask_emails:
        # Mask email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        masked = re.sub(email_pattern, '[EMAIL_MASKED]', masked)
    
    if mask_phones:
        # Mask phone numbers (basic patterns)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # XXX-XXX-XXXX or similar
            r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',  # (XXX) XXX-XXXX
        ]
        for pattern in phone_patterns:
            masked = re.sub(pattern, '[PHONE_MASKED]', masked)
    
    return masked