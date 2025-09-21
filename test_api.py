#!/usr/bin/env python3
"""
Test script to verify Google Gemini API key is working
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key or api_key == 'your_api_key_here':
    print("❌ No valid API key found!")
    print("Please add your Google AI Studio API key to the .env file")
    print("Get your API key from: https://aistudio.google.com/app/apikey")
    exit(1)

print(f"🔑 API Key found: {api_key[:10]}...")

try:
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Test API call
    print("🧪 Testing API call...")
    response = model.generate_content("Say 'Hello from Sakha.ai!' in a friendly way.")
    
    print("✅ API call successful!")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"❌ API call failed: {e}")
    print("Please check your API key and try again")
