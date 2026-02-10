import google.generativeai as genai
import os
import yaml

def list_models():
    # Load config to get key
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            api_key = config['ai']['gemini']['api_key']
            print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    genai.configure(api_key=api_key)

    print("Listing available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()