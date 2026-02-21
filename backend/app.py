from flask import Flask, request, jsonify, render_template
import json
import os
import requests
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("GEMINI_KEY")

print(f"API_KEY loaded: {'Yes' if API_KEY else 'No'}")

app = Flask(__name__)

# Load career dataset
with open('data/careers.json') as f:
    careers = json.load(f)

# Serve index.html at root URL
@app.route('/')
def home():
    return render_template('index.html')

# AI Generation function
def generate_ai_text(career, domain, skills, missing):
    if not missing:
        return "Congratulations! You have all the required skills for this career. Keep learning and expanding your knowledge!"
    
    prompt = f"""
You are an AI mentor for girls in STEM.

Domain: {domain}
Career goal: {career}
Current skills: {', '.join(skills)}
Missing skills: {', '.join(missing)}

Generate:
1. A step-by-step learning roadmap
2. Three game-like missions to level up
3. A short motivational message

Be encouraging and supportive. Keep it concise but helpful.
"""

    if not API_KEY:
        print("ERROR: GEMINI_KEY not found in .env file")
        return "AI mentor unavailable - please check your API key configuration"

    # Try with gemini-1.5-pro or gemini-pro
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={API_KEY}"

    try:
        print(f"Calling Gemini API...")
        response = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            },
            timeout=60
        )

        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return f"AI mentor unavailable - API error: {response.status_code}"
        
        data = response.json()
        print("GEMINI RESPONSE:", json.dumps(data, indent=2))

        if "candidates" in data and len(data["candidates"]) > 0:
            content = data["candidates"][0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                return parts[0].get("text", "AI returned empty response")
        
        return f"AI response format unexpected: {str(data)[:200]}"
        
    except requests.exceptions.Timeout:
        return "AI mentor is taking too long. Please try again."
    except Exception as e:
        print(f"AI generation error: {e}")
        return f"AI mentor is currently unavailable. Error: {str(e)}"

# Analyze POST route
@app.route('/analyze', methods=['POST'])
def analyze():
    # Get JSON data from request
    data = request.json
    
    career = data.get('career')
    domain = data.get('domain', 'Technology')
    user_skills = data.get('skills', [])
    
    # Print received JSON in terminal
    print("=" * 50)
    print("Received JSON:")
    print(data)
    print("=" * 50)
    
    # Get required skills for the career
    required = careers.get(career, [])
    
    # Calculate game stats
    if len(required) > 0:
        readiness = int((len(user_skills) / len(required)) * 100)
    else:
        readiness = 0
    
    xp = len(user_skills) * 50
    level = xp // 100
    missing = [s for s in required if s not in user_skills]
    
    # Generate AI text
    ai_text = generate_ai_text(career, domain, user_skills, missing)
    
    # Return JSON response with AI
    return jsonify({
        "career": career,
        "domain": domain,
        "readiness": readiness,
        "xp": xp,
        "level": level,
        "missing": missing,
        "ai_text": ai_text
    })

if __name__ == '__main__':
    app.run(debug=True)
