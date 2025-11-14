import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Check if the key was loaded
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    exit()

# Configure the API
genai.configure(api_key=GEMINI_API_KEY)

print("Connecting to Google to find your available models...\n")

try:
    # Iterate through all available models
    for m in genai.list_models():
        # We are looking for models that support 'generateContent'
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found usable model: {m.name}")
            print(f"   Supported methods: {m.supported_generation_methods}\n")

    print("\n--- End of list ---")
    print("Find a model in the list above (e.g., 'models/gemini-1.5-pro-latest' or 'models/gemini-pro')")
    print("and use that EXACT name in your watcher.py file.")

except Exception as e:
    print(f"An error occurred while trying to list models: {e}")
    print("\nThis likely means the NEW API key from 'Plan C' is still invalid or has not been enabled yet.")
    print("Please double-check your GEMINI_API_KEY in the .env file.")