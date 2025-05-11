import os
import google.generativeai as genai
from data_loader_st import load_constitution_text


genai.configure(api_key="AIzaSyAuzrzun2OIWlgUaR5HJY-3V-am6IsOLvE")

SYSTEM_PROMPT = (
    "You are an expert legal assistant.  "
    "You have the following constitutional text for the jurisdiction below.  "
    "Use ONLY that text plus your general legal knowledge to answer the user’s question clearly, "
    "citing specific articles where relevant, and offering practical next steps for real-world scenarios."
)

def get_ai_response_st(
    prompt: str,
    country: str,
    chat_history_for_llm: list
) -> str:
    """
    Pulls SYSTEM_PROMPT + constitution out of chat_history_for_llm,
    sends them as system_instruction, and then sends only user/model turns.
    """
    # 1) Append the new user prompt to our in-memory history
    chat_history_for_llm.append({
        "role": "user",
        "content": prompt
    })

    # 2) Extract and remove system messages
    system_parts = []
    filtered = []
    for turn in chat_history_for_llm:
        if turn["role"] == "system":
            system_parts.append(turn["content"])
        elif turn["role"] == "user":
            filtered.append({"role": "user", "parts": [turn["content"]]})
        elif turn["role"] == "assistant":
            # map your assistant → model
            filtered.append({"role": "model", "parts": [turn["content"]]})

    system_instruction = "\n\n".join(system_parts)

    try:
        # 3) Instantiate the model with system_instruction
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system_instruction
        )

        # 4) Start chat with only user/model history
        chat_session = model.start_chat(history=filtered)

        # 5) Send the latest user prompt
        response = chat_session.send_message(prompt)
        return response.text.strip()

    except Exception as e:
        return f"Error contacting Gemini API: {e}"