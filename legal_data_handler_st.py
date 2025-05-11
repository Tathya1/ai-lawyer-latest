"""
legal_data_handler_st.py
Handles loading the entire constitutional text as “legal context” 
for any user query, so that the LLM can reason over it.
"""
import os
from data_loader_st import load_constitution_text

def get_legal_context_st(country: str) -> str:
    """
    Always returns the full constitutional text (or an error message)
    so that the LLM has the entire document as background context.
    """
    return load_constitution_text(country)
