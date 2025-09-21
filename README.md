Sakha.ai - Your Compassionate Mental Health Companion
A web-based mental wellness companion that uniquely fuses the empathetic capabilities of modern AI with the timeless, profound wisdom of Indian philosophy and leadership. Sakha.ai is designed to be a safe, culturally resonant space for users to explore their feelings and find guidance for modern life's challenges.
✨ Core Features
💬 Multi-Mode AI Chat: Switch between Normal Mode (for empathetic, AI-driven conversations), Gita Mode (for wisdom from the Bhagavad Gita), and Leadership Mode (for motivation from great Indian leaders).
🌍 Multi-Lingual Support: Engage with Sakha.ai in multiple languages including English, Hindi, French, Spanish, Telugu, Tamil, and Punjabi for a more inclusive experience.
🚨 Proactive Crisis Support: Automatically detects keywords related to self-harm or acute distress and provides immediate access to professional emergency helplines.
📚 Curated Wisdom Database: The "Gita" and "Leadership" modes are powered by a structured backend database, ensuring the wisdom provided is reliable, relevant, and context-aware.
🌐 Responsive & Accessible UI: A clean, modern, and mobile-friendly interface built with vanilla HTML, CSS, and JavaScript for a seamless user experience on any device.
🔌 Offline Functionality: A Service Worker provides basic offline support, ensuring the app's interface loads even with an unstable or no internet connection.
🏛️ Architecture
The application runs on a simple but powerful architecture. The frontend is a static single-page application that communicates with a high-performance Python backend. The backend handles the core logic, including routing requests based on the selected mode to either the internal wisdom database or the external Google Gemini AI.
🛠️ Tech Stack
Layer
Technology
Purpose
Frontend
HTML, CSS, Vanilla JavaScript
For a fast, responsive, and universally accessible user interface.
Backend
Python 3.9+, FastAPI
To build a high-performance, scalable API for the chat service.
Core AI
Google Gemini API (gemini-1.5-flash)
To leverage a state-of-the-art AI for high-quality conversations.
Deployment
uvicorn
An ASGI server to run the FastAPI application.

🚀 Getting Started
Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.
Prerequisites
Python 3.9 or higher
A Google Gemini API Key
Installation
Clone the repository:
git clone [https://github.com/your-username/sakha-ai.git](https://github.com/your-username/sakha-ai.git)
cd sakha-ai


Create and activate a virtual environment:
On macOS/Linux:
python3 -m venv venv
source venv/bin/activate


On Windows:
python -m venv venv
.\venv\Scripts\activate


Install the required dependencies:
(Create a requirements.txt file with the content below, or install packages individually)
pip install -r requirements.txt

requirements.txt:
fastapi
uvicorn[standard]
python-dotenv
google-generativeai


Set up your environment variables:
Create a new file named .env in the root of the project directory.
Add your Google Gemini API Key to this file:
GOOGLE_API_KEY="YOUR_API_KEY_HERE"


Run the application:
uvicorn app:app --reload


Open your browser and navigate to http://127.0.0.1:8000. You should see the Sakha.ai welcome screen.
📁 File Structure
/
├── app.py              # FastAPI backend server logic
├── static/
│   ├── index.html      # Main frontend file
│   ├── style.css       # All CSS styles for the application
│   ├── script.js       # Frontend JavaScript logic for interactivity
│   └── sw.js           # Service Worker for offline support
├── .env                # Environment variables (needs to be created by you)
├── requirements.txt    # List of Python dependencies
└── README.md           # This file
