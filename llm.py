
    
"""
Integrates with Google Gemini (via google-generativeai) by feeding it:
  1) A system prompt to act as a legal assistant
  2) The full constitution text for the selected country
  3) The user’s question
Plus optional prior chat history for context.
"""

import os
import google.generativeai as genai
from data_loader_st import load_constitution_text

# Configure your Gemini API key (export GENAI_API_KEY in your env)
# NOTE: It is highly recommended NOT to hardcode API keys directly in code
# Use environment variables or a secure configuration management system instead.
# Example using os.getenv: genai.configure(api_key=os.getenv("GENAI_API_KEY"))
# For demonstration, keeping the hardcoded key from the original code snippet,
# but be aware of the security implications.
genai.configure(api_key="AIzaSyAuzrzun2OIWlgUaR5HJY-3V-am6IsOLvE")

SYSTEM_PROMPT = (
    "You are an expert legal assistant.  "
    "You have the following constitutional text for the jurisdiction below.  "
    "Use ONLY that text plus your general legal knowledge to answer the user’s question clearly, "
    "citing specific articles where relevant, and offering practical next steps for real-world scenarios."
)

def get_ai_response_st(prompt: str, country: str, chat_history_for_llm: list) -> str:
    """
    Sends the constitution + user prompt to Google Gemini and returns its answer.
    Falls back to an error message if the constitution file is missing/empty.
    """
    # 1) Load the full constitution text
    constitution = load_constitution_text(country)
    if "not found" in constitution or "empty" in constitution.lower():
        return constitution

    # 2) Build the chat messages list for Gemini
    messages = [
        # Note: The genai.ChatCompletion API might handle the system prompt differently
        # or require it to be part of the initial message.
        # For newer Gemini models (like 1.5 Flash), the standard is often
        # a list of "parts" within a "role".
        # This structure might need adjustment depending on the specific version
        # of the google-generativeai library and the model's expected input format.
        # A common pattern for chat is user/model turns. Let's keep the original
        # structure for now but be aware it might need adaptation for newer models.
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"--- CONSTITUTION OF {country.upper()} ---\n{constitution}"},
    ]

    # 3) Append any prior conversation for continuity
    # The roles 'user' and 'assistant' (or 'model' for newer Gemini) are standard
    for turn in chat_history_for_llm:
        messages.append({
            "role": turn["role"],
            "content": turn["content"]
        })

    # 4) Add the current user question
    messages.append({"role": "user", "content": prompt})

    # 5) Call Gemini via the API
    try:
        # Use the newer genai.GenerativeModel interface for Gemini models
        # The ChatCompletion interface might be deprecated or behave differently.
        # System instructions are handled separately for newer models.
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", # Using a common identifier for Gemini Flash
            system_instruction=SYSTEM_PROMPT + f"\n--- CONSTITUTION OF {country.upper()} ---\n{constitution}"
        )

        # Prepare history for the new chat session format (list of history turns)
        # Note: The system instruction is handled by the model setup, not history.
        # The constitution is also part of the system instruction.
        # History should only contain user/model turns.
        chat_history_for_model = []
        # Assuming chat_history_for_llm uses roles like 'user' and 'assistant'/'model'
        for turn in chat_history_for_llm:
             chat_history_for_model.append({
                 "role": turn["role"], # Should be 'user' or 'model'
                 "parts": [turn["content"]]
             })


        chat_session = model.start_chat(history=chat_history_for_model)

        response = chat_session.send_message(prompt)

        # Extract and return the assistant’s reply
        # Response structure might vary; typically it's response.text
        return response.text.strip()

    except Exception as e:
        # Catch potential errors like API key issues, rate limits, etc.
        return f"Error contacting Gemini API: {e}"

# Note: The original code used genai.ChatCompletion.create which is typical
# for older models like chat-bison. Gemini models (like 1.5 Flash) are
# typically accessed via genai.GenerativeModel and its start_chat method.
# The code above has been updated to use the newer GenerativeModel approach
# and the 'gemini-1.5-flash-latest' model name.



