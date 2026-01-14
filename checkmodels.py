# check_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ No API Key found in .env file.")
else:
    print(f"✅ Key found: {api_key[:5]}...")
    genai.configure(api_key=api_key)
    
    print("\nAttempting to list available models...")
    try:
        # We list all models and filter for ones that can generate text
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"❌ Error contacting Google: {e}")