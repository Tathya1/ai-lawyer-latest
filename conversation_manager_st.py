"""
conversation_manager_st.py
Manages chat history using Streamlit's session state (passed as an argument).
"""
import json
import uuid
from streamlit_local_storage import get_local_chat_history, save_chat_to_local_storage, delete_local_chat, get_all_chat_ids

def initialize_chat_history(st_session_state):
    """Initializes chat history in Streamlit's session state if not present."""
    if "messages" not in st_session_state:
        st_session_state.messages = []  # Each item: {"role": "user/assistant/system", "content": "..."}
    if "current_country" not in st_session_state:
        st_session_state.current_country = "Japan"  # Default country
    if "chat_ids" not in st_session_state:
        st_session_state.chat_ids = {}  # Maps chat names to unique IDs
        
def ensure_chat_id(st_session_state, chat_name):
    """Ensures each chat has a unique ID for local storage."""
    if "chat_ids" not in st_session_state:
        st_session_state.chat_ids = {}
        
    if chat_name not in st_session_state.chat_ids:
        st_session_state.chat_ids[chat_name] = str(uuid.uuid4())
    
    return st_session_state.chat_ids[chat_name]

def add_to_history_st(st_session_state, role: str, content: str):
    """Adds a message to the chat history in Streamlit's session state."""
    st_session_state.messages.append({"role": role, "content": content})

def clear_history_st(st_session_state):
    """Clears the chat history in Streamlit's session state."""
    st_session_state.messages = []
    # We don't reset current_country here - we'll handle that elsewhere
    return "Chat history cleared. The AI will not remember this conversation in the current session."

def get_history_for_llm(st_session_state) -> list:
    """Returns the chat history in a format suitable for LLM APIs."""
    return st_session_state.messages[:]  # Return a copy

def get_chat_history_from_local(st_session_state, chat_name):
    """Gets chat history from local storage for a specific chat."""
    chat_id = ensure_chat_id(st_session_state, chat_name)
    history_json = get_local_chat_history(chat_id)
    try:
        return json.loads(history_json)
    except (json.JSONDecodeError, TypeError):
        return []

def save_chat_history_to_local(st_session_state, chat_name, messages):
    """Saves chat history to local storage for a specific chat."""
    chat_id = ensure_chat_id(st_session_state, chat_name)
    save_chat_to_local_storage(chat_id, messages)

def delete_chat_from_local(st_session_state, chat_name):
    """Deletes chat history from local storage for a specific chat."""
    chat_id = ensure_chat_id(st_session_state, chat_name)
    delete_local_chat(chat_id)
    # Also remove from chat_ids
    if chat_name in st_session_state.chat_ids:
        del st_session_state.chat_ids[chat_name]