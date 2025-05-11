import streamlit as st
import os
import json
import sqlite3
from glob import glob

# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Lawyer", page_icon="⚖️", layout="wide")

from country_selector_st import SUPPORTED_COUNTRIES
from data_loader_st import DATA_DIR, load_constitution_text
from legal_data_handler_st import get_legal_context_st
from llm_integration_st import get_ai_response_st, SYSTEM_PROMPT
from conversation_manager_st import (
    initialize_chat_history,
    add_to_history_st,
    clear_history_st,
    get_history_for_llm
)

CHAT_DIR = os.path.join(DATA_DIR, "chat")
DB_PATH  = os.path.join(DATA_DIR, "stats.db")
os.makedirs(CHAT_DIR, exist_ok=True)

# ─── Load individual chat files ───────────────────────────────────────────────
def load_chats_from_disk():
    chats = {}
    for path in glob(os.path.join(CHAT_DIR, "*.json")):
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            chats[name] = json.load(f)
    return chats or {"Chat 1": {"country": None, "messages": [], "const_loaded_for": None}}

def save_chat_to_disk(chat_name, data):
    path = os.path.join(CHAT_DIR, f"{chat_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_chat_from_disk(chat_name):
    path = os.path.join(CHAT_DIR, f"{chat_name}.json")
    if os.path.exists(path):
        os.remove(path)

# ─── Initialize Chat State ────────────────────────────────────────────────────
if "chats" not in st.session_state:
    st.session_state.chats = load_chats_from_disk()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = next(iter(st.session_state.chats))

if st.session_state.current_chat not in st.session_state.chats:
    st.session_state.current_chat = next(iter(st.session_state.chats))

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stButton>button { border-radius: 5px; padding: 10px 15px; }
  .stTextInput>div>div>input { border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ─── Current Chat State ───────────────────────────────────────────────────────
active = st.session_state.chats[st.session_state.current_chat]
st.session_state.messages         = active["messages"]
st.session_state.const_loaded_for = active["const_loaded_for"]
st.session_state.current_country  = active["country"] or list(SUPPORTED_COUNTRIES.keys())[0]

# ─── Initialize Chat Context ──────────────────────────────────────────────────
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

active["country"]          = st.session_state.current_country
active["const_loaded_for"] = st.session_state.const_loaded_for
active["messages"]         = st.session_state.messages

# ─── SQLite Setup ─────────────────────────────────────────────────────────────
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

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚖️ AI Lawyer")
    st.markdown("---")

    if st.button("➕ New Chat"):
        idx = len(st.session_state.chats) + 1
        new_name = f"Chat {idx}"
        st.session_state.chats[new_name] = {
            "country": None, "messages": [], "const_loaded_for": None
        }
        st.session_state.current_chat = new_name
        save_chat_to_disk(new_name, st.session_state.chats[new_name])
        st.rerun()

    st.markdown("#### Your Chats")
    for name in st.session_state.chats:
        if name == st.session_state.current_chat:
            st.markdown(f"**• {name}**")
        else:
            if st.button(name, key=f"select_{name}"):
                st.session_state.current_chat = name
                st.rerun()

    st.markdown("---")
    sel = st.selectbox(
        "Jurisdiction",
        list(SUPPORTED_COUNTRIES.keys()),
        index=list(SUPPORTED_COUNTRIES.keys()).index(st.session_state.current_country),
        format_func=lambda k: SUPPORTED_COUNTRIES[k]
    )
    if sel != st.session_state.current_country:
        st.session_state.current_country = sel
        st.session_state.const_loaded_for = None
        st.rerun()

    st.markdown("---")
    st.info("This is a just a prototype. Please consult a lawyer for serious matters.")

# ─── Main Chat UI ─────────────────────────────────────────────────────────────
st.title(f"{SUPPORTED_COUNTRIES[st.session_state.current_country]}")
st.caption(f"Chat: {st.session_state.current_chat}")

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Your question…"):
    add_to_history_st(st.session_state, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            hist = get_history_for_llm(st.session_state)
            ai_resp = get_ai_response_st(prompt, st.session_state.current_country, hist)
            st.markdown(ai_resp)

    add_to_history_st(st.session_state, "assistant", ai_resp)
    active["messages"] = st.session_state.messages

    save_chat_to_disk(st.session_state.current_chat, active)

    cat = categorize_question(prompt, ai_resp)
    con = init_db()
    con.execute("""
      INSERT INTO question_stats(category, count)
      VALUES (?, 1)
      ON CONFLICT(category) DO UPDATE SET count = count + 1
    """, (cat,))
    con.close()

if st.button("🗑️ Delete Chat", key="delete_chat"):
    delete_chat_from_disk(st.session_state.current_chat)
    del st.session_state.chats[st.session_state.current_chat]
    if not st.session_state.chats:
        st.session_state.chats["Chat 1"] = {
            "country": None, "messages": [], "const_loaded_for": None
        }
    st.session_state.current_chat = next(iter(st.session_state.chats))
    st.rerun()
