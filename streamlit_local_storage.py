import streamlit.components.v1 as components
import json

def get_local_chat_history(country_key: str):
    components.html(f"""
    <script>
      const key = "aiLawyer_history_{country_key}";
      const history = localStorage.getItem(key) || "[]";
      const streamlitEvent = new CustomEvent("streamlit:componentReady", {{
        detail: {{ returnValue: history }}
      }});
      window.parent.document.dispatchEvent(streamlitEvent);
    </script>
    """, height=0)

def save_chat_to_local_storage(country_key: str, history_list: list):
    json_history = json.dumps(history_list).replace('"', '&quot;')
    components.html(f"""
    <script>
      const key = "aiLawyer_history_{country_key}";
      localStorage.setItem(key, "{json_history}");
    </script>
    """, height=0)

def delete_local_chat(country_key: str):
    components.html(f"""
    <script>
      const key = "aiLawyer_history_{country_key}";
      localStorage.removeItem(key);
    </script>
    """, height=0)
