"""
conversation_manager_st.py
Manages chat history using Streamlit's session state (passed as an argument).
"""

def initialize_chat_history(st_session_state):
    """Initializes chat history in Streamlit's session state if not present."""
    if "messages" not in st_session_state:
        st_session_state.messages = []  # Each item: {"role": "user/assistant/system", "content": "..."}
    if "current_country" not in st_session_state:
        st_session_state.current_country = "Japan"  # Default country

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