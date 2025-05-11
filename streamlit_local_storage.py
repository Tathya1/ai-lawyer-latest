import streamlit.components.v1 as components
import json

def get_local_chat_history(chat_id: str):
    """Get chat history from local storage for a specific chat ID."""
    components.html(f"""
    <script>
      const key = "aiLawyer_chat_{chat_id}";
      const history = localStorage.getItem(key) || "[]";
      const streamlitEvent = new CustomEvent("streamlit:componentReady", {{
        detail: {{ returnValue: history }}
      }});
      window.parent.document.dispatchEvent(streamlitEvent);
    </script>
    """, height=0)

def save_chat_to_local_storage(chat_id: str, history_list: list):
    """Save chat history to local storage for a specific chat ID."""
    json_history = json.dumps(history_list).replace('"', '&quot;')
    components.html(f"""
    <script>
      const key = "aiLawyer_chat_{chat_id}";
      localStorage.setItem(key, "{json_history}");
    </script>
    """, height=0)

def delete_local_chat(chat_id: str):
    """Delete chat history from local storage for a specific chat ID."""
    components.html(f"""
    <script>
      const key = "aiLawyer_chat_{chat_id}";
      localStorage.removeItem(key);
    </script>
    """, height=0)

def get_all_chat_ids():
    """Get all chat IDs from local storage."""
    components.html("""
    <script>
      const prefix = "aiLawyer_chat_";
      const chatIds = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith(prefix)) {
          chatIds.push(key.substring(prefix.length));
        }
      }
      const streamlitEvent = new CustomEvent("streamlit:componentReady", {
        detail: { returnValue: JSON.stringify(chatIds) }
      });
      window.parent.document.dispatchEvent(streamlitEvent);
    </script>
    """, height=0)
