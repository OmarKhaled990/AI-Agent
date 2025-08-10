# backend/graph.py
import os
import json
from typing import Dict, List, Any, TypedDict, Optional
from langgraph.graph import StateGraph, END
from groq import Groq
from datetime import datetime
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    user_profile: Dict[str, Any]
    guidelines: str
    summary: str
    context: str
    knowledge_base: List[Dict[str, str]]
    metadata: Dict[str, Any]

def load_context(state: AgentState) -> AgentState:
    """Load system context and prepare the conversation"""
    try:
        # Build comprehensive system prompt
        base_prompt = state.get('guidelines', 'You are a helpful AI assistant.')
        
        # Add knowledge base context if available
        kb_context = ""
        if state.get('knowledge_base'):
            kb_context = "\n\nRelevant knowledge base information:\n"
            for kb_item in state['knowledge_base'][:3]:  # Limit to top 3 relevant items
                kb_context += f"- {kb_item.get('content', '')}\n"
        
        # Add user profile context
        user_context = ""
        if state.get('user_profile'):
            profile = state['user_profile']
            if profile.get('name'):
                user_context += f"\nUser's name: {profile['name']}"
            if profile.get('preferences'):
                user_context += f"\nUser preferences: {profile['preferences']}"
        
        # Add conversation summary
        summary_context = ""
        if state.get('summary'):
            summary_context = f"\n\nConversation history summary:\n{state['summary']}"
        
        # Combine all context
        system_prompt = (
            f"{base_prompt}\n"
            f"{user_context}\n"
            f"{summary_context}\n"
            f"{kb_context}\n\n"
            "Instructions:\n"
            "- Be helpful, accurate, and conversational\n"
            "- Use the knowledge base information when relevant\n"
            "- Remember the conversation context\n"
            "- Ask clarifying questions when needed\n"
            "- Keep responses concise but informative"
        )
        
        # Prepare messages with system prompt
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(state.get("messages", []))
        
        state["messages"] = messages
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["context_loaded_at"] = datetime.utcnow().isoformat()
        
        return state
        
    except Exception as e:
        logger.error(f"Error in load_context: {e}")
        # Fallback to basic system prompt
        system_prompt = state.get('guidelines', 'You are a helpful AI assistant.')
        state["messages"] = [{"role": "system", "content": system_prompt}] + state.get("messages", [])
        return state

def retrieve_knowledge(state: AgentState) -> AgentState:
    """Retrieve relevant knowledge from knowledge base"""
    try:
        # Extract the last user message for context
        user_messages = [msg for msg in state.get("messages", []) if msg.get("role") == "user"]
        if not user_messages:
            return state
        
        last_user_message = user_messages[-1].get("content", "")
        
        # Simple keyword-based retrieval (in production, use vector embeddings)
        knowledge_base = state.get("knowledge_base", [])
        if knowledge_base and last_user_message:
            # Score documents based on keyword overlap (simplified)
            scored_docs = []
            keywords = last_user_message.lower().split()
            
            for doc in knowledge_base:
                content = doc.get("content", "").lower()
                score = sum(1 for keyword in keywords if keyword in content)
                if score > 0:
                    scored_docs.append((score, doc))
            
            # Sort by relevance and take top results
            scored_docs.sort(reverse=True, key=lambda x: x[0])
            state["knowledge_base"] = [doc for score, doc in scored_docs[:5]]
        
        return state
        
    except Exception as e:
        logger.error(f"Error in retrieve_knowledge: {e}")
        return state

def llm_reply(state: AgentState) -> AgentState:
    """Generate LLM response"""
    try:
        # Extract model parameters from metadata
        metadata = state.get("metadata", {})
        model = metadata.get("model", "llama-3.1-8b-instant")
        temperature = metadata.get("temperature", 0.3)
        max_tokens = metadata.get("max_tokens", 1000)
        
        # Ensure temperature is within valid range
        temperature = max(0.0, min(2.0, temperature))
        
        # Make API call to Groq
        start_time = datetime.utcnow()
        
        response = client.chat.completions.create(
            model=model,
            messages=state["messages"],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            stream=False
        )
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        # Extract reply
        reply = response.choices[0].message.content
        
        # Add response to conversation
        state["messages"].append({"role": "assistant", "content": reply})
        
        # Update metadata
        state["metadata"].update({
            "response_time": response_time,
            "model_used": model,
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
            "generated_at": end_time.isoformat()
        })
        
        return state
        
    except Exception as e:
        logger.error(f"Error in llm_reply: {e}")
        # Fallback response
        fallback_reply = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
        state["messages"].append({"role": "assistant", "content": fallback_reply})
        state["metadata"]["error"] = str(e)
        return state

def post_process(state: AgentState) -> AgentState:
    """Post-process the response"""
    try:
        # Log interaction for analytics
        metadata = state.get("metadata", {})
        metadata["processed_at"] = datetime.utcnow().isoformat()
        
        # Could add additional processing here:
        # - Content filtering
        # - Response quality checking
        # - Custom formatting
        
        return state
        
    except Exception as e:
        logger.error(f"Error in post_process: {e}")
        return state

# Build the graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("load_context", load_context)
graph.add_node("retrieve_knowledge", retrieve_knowledge)
graph.add_node("llm_reply", llm_reply)
graph.add_node("post_process", post_process)

# Add edges
graph.add_edge("load_context", "retrieve_knowledge")
graph.add_edge("retrieve_knowledge", "llm_reply")
graph.add_edge("llm_reply", "post_process")
graph.add_edge("post_process", END)

# Set entry point
graph.set_entry_point("load_context")

# Compile the graph
compiled_graph = graph.compile()

def run_agent_with_memory(
    messages: List[Dict[str, str]], 
    user_profile: Dict[str, Any], 
    guidelines: str, 
    summary: str,
    knowledge_base: Optional[List[Dict[str, str]]] = None,
    model_config: Optional[Dict[str, Any]] = None
) -> str:
    """Run the agent with enhanced memory and knowledge base support"""
    try:
        # Prepare initial state
        init_state: AgentState = {
            "messages": messages or [],
            "user_profile": user_profile or {},
            "guidelines": guidelines or "You are a helpful assistant.",
            "summary": summary or "",
            "context": "",
            "knowledge_base": knowledge_base or [],
            "metadata": model_config or {}
        }
        
        # Run the graph
        final_state = compiled_graph.invoke(init_state)
        
        # Extract the assistant's response
        assistant_messages = [
            msg for msg in final_state["messages"] 
            if msg.get("role") == "assistant"
        ]
        
        if assistant_messages:
            return assistant_messages[-1].get("content", "")
        
        return "I apologize, but I couldn't generate a response. Please try again."
        
    except Exception as e:
        logger.error(f"Error in run_agent_with_memory: {e}")
        return "I'm experiencing technical difficulties. Please try again in a moment."

def summarize_history(summary: str, tail: List[Dict[str, str]]) -> str:
    """Create or update conversation summary"""
    try:
        if not tail:
            return summary or ""
        
        # Prepare prompt for summarization
        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You are a conversation summarizer. Create a concise summary of the conversation "
                    "that captures key information, user preferences, and important context. "
                    "Keep it under 200 words and focus on actionable information."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Current summary: {summary or '(No previous summary)'}\n\n"
                    f"Recent conversation:\n" +
                    "\n".join([
                        f"{msg['role'].title()}: {msg['content']}" 
                        for msg in tail[-10:]  # Last 10 messages
                    ]) +
                    "\n\nPlease update the summary with new information from this conversation."
                )
            }
        ]
        
        # Generate summary
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=prompt_messages,
            temperature=0.2,
            max_tokens=300
        )
        
        new_summary = response.choices[0].message.content.strip()
        return new_summary
        
    except Exception as e:
        logger.error(f"Error in summarize_history: {e}")
        # Fallback: keep existing summary or create basic one
        if summary:
            return summary
        
        # Create basic summary from recent messages
        user_messages = [msg["content"] for msg in tail if msg.get("role") == "user"]
        if user_messages:
            return f"User discussed: {', '.join(user_messages[-3:])}"
        
        return "New conversation started."

# Enhanced function for model testing
async def test_model_response(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1000
) -> Dict[str, Any]:
    """Test a model configuration"""
    try:
        start_time = datetime.utcnow()
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "response_time": response_time,
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
            "model": model
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model
        }

# Knowledge base search function
def search_knowledge_base(
    query: str, 
    documents: List[Dict[str, str]], 
    limit: int = 5
) -> List[Dict[str, str]]:
    """Search knowledge base documents"""
    try:
        if not documents or not query:
            return []
        
        # Simple keyword-based search (in production, use vector embeddings)
        query_words = set(query.lower().split())
        scored_docs = []
        
        for doc in documents:
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()
            
            # Calculate relevance score
            content_matches = sum(1 for word in query_words if word in content)
            title_matches = sum(2 for word in query_words if word in title)  # Title matches weighted higher
            
            total_score = content_matches + title_matches
            if total_score > 0:
                scored_docs.append((total_score, doc))
        
        # Sort by relevance and return top results
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        return [doc for score, doc in scored_docs[:limit]]
        
    except Exception as e:
        logger.error(f"Error in search_knowledge_base: {e}")
        return []