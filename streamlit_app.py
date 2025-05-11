import streamlit as st
# ─── Page config must be first (no other Streamlit imports/code before this) ─────────────────
st.set_page_config(page_title="AI Lawyer", page_icon="⚖️", layout="wide")

# ─── Other imports ─────────────────────────────────────────────────────────────
import os
import json
import sqlite3
import uuid
from streamlit_cookies_manager import EncryptedCookieManager

from country_selector_st import SUPPORTED_COUNTRIES
from data_loader_st import DATA_DIR, load_constitution_text
from legal_data_handler_st import get_legal_context_st
from llm_integration_st import get_ai_response_st, SYSTEM_PROMPT
from conversation_manager_st import (
    initialize_chat_history,
    add_to_history_st,
    clear_history_st,
    get_history_for_llm,
    get_chat_history_from_local,
    save_chat_history_to_local,
    delete_chat_from_local
) 

# ─── Cookie manager for persistent session ID ─────────────────────────────────
cookies = EncryptedCookieManager(
    prefix="ai_lawyer_",
    password="YOUR_SECURE_32_BYTE_PASSWORD_123456"
)
if not cookies.ready():
    st.stop()

sid = cookies.get("sid")
if sid is None:
    sid = str(uuid.uuid4())
    cookies["sid"] = sid
    cookies.save()

# ─── Storage setup ─────────────────────────────────────────────────────────────
CHAT_DIR = os.path.join(DATA_DIR, "chat_sessions")
os.makedirs(CHAT_DIR, exist_ok=True)
SESSION_FILE = os.path.join(CHAT_DIR, f"{sid}.json")

# ─── Load or initialize session data (multiple chats) ─────────────────────────
if os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        session_data = json.load(f)
else:
    # Default single chat on new session
    session_data = {
        "current_chat": "Chat 1",
        "chats": {
            "Chat 1": {"country": None, "messages": [], "const_loaded_for": None}
        }
    }
# Ensure structure and non-empty chats
if "chats" not in session_data or not session_data.get("chats"):
    session_data = {
        "current_chat": "Chat 1",
        "chats": {"Chat 1": {"country": None, "messages": [], "const_loaded_for": None}}
    }
# Validate current_chat key
if session_data.get("current_chat") not in session_data["chats"]:
    session_data["current_chat"] = next(iter(session_data["chats"]))

# Initialize session state
if "chats" not in st.session_state:
    st.session_state.chats = session_data["chats"]
if "current_chat" not in st.session_state:
    st.session_state.current_chat = session_data["current_chat"]

# Shortcut to active chat data
active = st.session_state.chats.get(st.session_state.current_chat)
if active is None:
    # Fallback to first chat
    first = next(iter(st.session_state.chats))
    st.session_state.current_chat = first
    active = st.session_state.chats[first]

# ─── Initialize chat state from active data ────────────────────────────────────
if "current_country" not in st.session_state:
    st.session_state.current_country = active.get("country") or list(SUPPORTED_COUNTRIES.keys())[0]
if "messages" not in st.session_state:
    st.session_state.messages = active.get("messages", [])
if "const_loaded_for" not in st.session_state:
    st.session_state.const_loaded_for = active.get("const_loaded_for")

# ─── Load or refresh constitution into history ─────────────────────────────────
initialize_chat_history(st.session_state)
if st.session_state.const_loaded_for != st.session_state.current_country:
    clear_history_st(st.session_state)
    raw_const = load_constitution_text(st.session_state.current_country)
    add_to_history_st(st.session_state, "system", SYSTEM_PROMPT)
    add_to_history_st(
        st.session_state,
        "system",
        f"--- CONSTITUTION OF {st.session_state.current_country.upper()} ---\n{raw_const}"
    )
    st.session_state.const_loaded_for = st.session_state.current_country

# ─── Save session_data back to file ────────────────────────────────────────────
def save_session():
    # update active data
    active = st.session_state.chats[st.session_state.current_chat]
    active["country"] = st.session_state.current_country
    active["messages"] = st.session_state.messages
    active["const_loaded_for"] = st.session_state.const_loaded_for

    session_data = {
        "current_chat": st.session_state.current_chat,
        "chats": st.session_state.chats,
        "chat_ids": st.session_state.chat_ids if "chat_ids" in st.session_state else {}
    }
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    # Also save to local storage
    save_chat_history_to_local(st.session_state, st.session_state.current_chat, st.session_state.messages)

# ─── Handlers for chat management ───────────────────────────────────────────────
def create_new_chat():
    idx = len(st.session_state.chats) + 1
    new_name = f"Chat {idx}"
    st.session_state.chats[new_name] = {
        "country": st.session_state.current_country, 
        "messages": [], 
        "const_loaded_for": None
    }
    st.session_state.current_chat = new_name
    st.session_state.messages = []
    st.session_state.const_loaded_for = None
    save_session()
    st.rerun()
    
def switch_to_chat(name):
    st.session_state.current_chat = name
    active = st.session_state.chats[name]
    st.session_state.current_country = active.get("country") or list(SUPPORTED_COUNTRIES.keys())[0]
    
    # Load messages from local storage if available
    local_messages = get_chat_history_from_local(st.session_state, name)
    if local_messages and len(local_messages) > 0:
        st.session_state.messages = local_messages
    else:
        st.session_state.messages = active.get("messages", [])
        
    st.session_state.const_loaded_for = active.get("const_loaded_for")
    save_session()
    st.rerun()
    
def delete_current_chat():
    if len(st.session_state.chats) > 1:
        # Get chat to delete
        chat_to_delete = st.session_state.current_chat
        
        # Delete from local storage
        delete_chat_from_local(st.session_state, chat_to_delete)
        
        # Remove from state
        del st.session_state.chats[chat_to_delete]
        
        # Switch to another chat
        st.session_state.current_chat = next(iter(st.session_state.chats))
        active = st.session_state.chats[st.session_state.current_chat]
        
        # Load messages from local storage for the new active chat
        local_messages = get_chat_history_from_local(st.session_state, st.session_state.current_chat)
        if local_messages and len(local_messages) > 0:
            st.session_state.messages = local_messages
        else:
            st.session_state.messages = active.get("messages", [])
            
        st.session_state.current_country = active.get("country") or list(SUPPORTED_COUNTRIES.keys())[0]
        st.session_state.const_loaded_for = active.get("const_loaded_for")
        
        # Save changes
        save_session()
        st.rerun()
    else:
        # Don't delete the last chat, just clear it
        clear_history_st(st.session_state)
        st.session_state.const_loaded_for = None
        save_session()
        st.rerun()

# ─── SQLite Stats (in-memory) ─────────────────────────────────────────────────
DB_PATH = ":memory:"
def init_db():
    con = sqlite3.connect(DB_PATH, isolation_level=None)
    cur = con.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS question_stats (
        category TEXT PRIMARY KEY,
        count    INTEGER NOT NULL DEFAULT 0
      )
    """)
    return con

# ─── Categories ───────────────────────────────────────────────────────────────
CATEGORIES = {
    "Constitutional": [
        "constitution","article","amendment","fundamental rights",
        "separation of powers","due process","judicial review",
        "bill of rights","charter","sovereignty","preamble",
        "federalism","state","federal","legislature",
        "executive","judiciary","clause","ratification","entrenchment"
    ],
    "Criminal": [
        "crime","punishment","penal","sentence","offense","felony",
        "misdemeanor","prosecution","conviction","acquittal","bail",
        "custody","arrest","police","investigation","indictment",
        "plea","trial","jurors","homicide","assault","theft",
        "fraud","bribery","embezzlement","racketeering",
        "drug trafficking","weapon","manslaughter"
    ],
    "Civil": [
        "contract","tort","liability","damages","negligence",
        "breach","indemnification","specific performance",
        "injunction","equity","trust","estate","inheritance",
        "property","landlord","tenant","lease","mortgage",
        "easement","boundary","defamation","libel","slander"
    ],
    "Procedure": [
        "jurisdiction","procedure","filing","appeal","motion",
        "pleading","summary judgment","discovery","evidence",
        "hearing","order","judgment","clerk","subpoena","affidavit",
        "deposition","court fees","venue","statute of limitations"
    ],
    "Family": [
        "marriage","divorce","custody","adoption","alimony",
        "child support","guardianship","paternity","domestic violence",
        "prenuptial","postnuptial","visitation","annulment"
    ],
    "Administrative": [
        "regulation","license","permit","administrative",
        "agency","rulemaking","compliance","inspection",
        "zoning","planning","environmental","immigration","visa"
    ],
    "Tax": [
        "tax","duty","vat","income tax","capital gains","withholding",
        "sales tax","excise","property tax","tax credit","deduction",
        "audit","penalty","customs","estate tax"
    ],
    "Labor & Employment": [
        "employment","labor","wage","overtime","union",
        "discrimination","harassment","termination","benefits",
        "minimum wage","leave","occupational safety"
    ],
    "Commercial & Corporate": [
        "company","corporation","director","shareholder","merger",
        "acquisition","joint venture","partnership","ipo",
        "securities","antitrust","competition","franchise"
    ],
    "Intellectual Property": [
        "trademark","copyright","patent","trade secret","licensing",
        "infringement","fair use","royalty","registration"
    ],
    "Immigration & Nationality": [
        "citizenship","naturalization","immigration","asylum",
        "refugee","deportation","residency","stateless"
    ],
    "Environmental": [
        "environmental","pollution","emissions","conservation",
        "wildlife","waste","climate change","carbon","ozone"
    ],
    "Other": []
}

def categorize_question(prompt, response):
    txt = (prompt + " " + response).lower()
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if kw in txt:
                return cat
    return "Other"

# ─── Sidebar: Chats and Jurisdiction ───────────────────────────────────────────
with st.sidebar:
    st.title("⚖️ AI Lawyer")
    st.markdown("---")

    # New Chat button
    if st.button("➕ New Chat"):
        create_new_chat()

    st.markdown("**Your Chats:**")
    for name in st.session_state.chats:
        if name == st.session_state.current_chat:
            st.markdown(f"- **{name}**")
        else:
            if st.button(name, key=f"select_{name}"):
                switch_to_chat(name)
                
    st.markdown("---")
    sel = st.selectbox(
        "Jurisdiction",
        list(SUPPORTED_COUNTRIES.keys()),
        index=list(SUPPORTED_COUNTRIES.keys()).index(st.session_state.current_country),
        format_func=lambda k: SUPPORTED_COUNTRIES[k],
        key="current_country"
    )
    if sel != st.session_state.current_country:
        st.session_state.current_country = sel
        st.session_state.const_loaded_for = None
        save_session()
        st.rerun()

# ─── Main Chat UI ─────────────────────────────────────────────────────────────
st.title(f"{SUPPORTED_COUNTRIES[st.session_state.current_country]}")
st.caption(f"Chat: {st.session_state.current_chat}")

for msg in st.session_state.messages:
    if msg.get("role") != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Place Delete Chat button bottom-right
col1, col2, col3 = st.columns([1,1,1])
with col3:
    if st.button("🗑️ Delete Chat"):
        delete_current_chat()

# ─── Handle user input ─────────────────────────────────────────────────────────
if prompt := st.chat_input("Your question…"):
    add_to_history_st(st.session_state, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            hist = get_history_for_llm(st.session_state)
            ai_resp = get_ai_response_st(
                prompt, 
                st.session_state.current_country, 
                hist,
                temperature=0.2,
                top_p=0.95,
                candidate_count=1
            )
            st.markdown(ai_resp)

    add_to_history_st(st.session_state, "assistant", ai_resp)
    save_session()

    # update stats
    con = init_db()
    cat = categorize_question(prompt, ai_resp)
    con.execute(
        """
        INSERT INTO question_stats(category, count)
        VALUES (?, 1)
        ON CONFLICT(category) DO UPDATE SET count = count + 1
        """,
        (cat,)
    )
    con.close()
