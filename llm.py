# app/services/llm.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq Client
# It automatically looks for "GROQ_API_KEY" in your environment
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_gpt_response(system_prompt: str, user_prompt: str):
    """
    Uses Groq (Llama 3.3 70B) for lightning-fast, essentially unlimited responses.
    """
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            # We use Llama 3.3 70B (Smarter) or Llama 3.1 8B (Faster)
            # Both have massive free limits (1k - 14k requests/day)
            model="llama-3.3-70b-versatile", 
            
            # Optional: controls creativity (0.0 = Robot, 1.0 = Poet)
            temperature=0.7,
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"AI Error: {str(e)}"