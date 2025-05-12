"""
llm_integration_st.py
Integration with LLM APIs.
"""
import google.generativeai as genai

# Initialize the Google Generative AI API
GOOGLE_API_KEY = "AIzaSyAh637ZJqYpG-PSj0aXpzXnWuy09cGs0aw"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)

# System prompt
SYSTEM_PROMPT = """You are an AI legal assistant specializing in constitutional law.
Your purpose is to provide accurate information about constitutional rights and legal procedures.
Base your responses on the constitution text provided to you.
If you're unsure about anything, admit that you don't know rather than providing potentially incorrect information.
Do not make up laws or constitutional provisions that do not exist.
Also cite specific articles where relevant, and offer practical next steps for real-world scenarios.
"""

def get_ai_response_st(
    prompt: str,
    country: str,
    history: list,
    temperature=0.2,
    top_p=0.95,
    candidate_count=1
):
    """
    Gets a response from the AI model based on the conversation history.
    
    Args:
        prompt: The user's question or prompt
        country: The country whose legal system we're discussing
        history: List of conversation messages in the format [{"role": "...", "content": "..."}]
        temperature: Controls randomness of output (0.0-1.0), lower is more deterministic
        top_p: Controls diversity via nucleus sampling (0.0-1.0)
        candidate_count: Number of response candidates to generate
        
    Returns:
        The AI's response as a string
    """
    try:
        # Use the PaLM API or any other LLM API here
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "temperature": temperature,
                "top_p": top_p,
                "candidate_count": candidate_count,
                "max_output_tokens": 2048,
            }
        )
        
        # Format the conversation for the model
        formatted_history = []
        for msg in history:
            if msg["role"] == "user":
                formatted_history.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                formatted_history.append({"role": "model", "parts": [msg["content"]]})
            # System messages are handled differently for Gemini

        # Create a chat session
        chat = model.start_chat(history=formatted_history)
        
        # Get the response
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"I encountered an error: {str(e)}. Please try rephrasing your question or try again later."
