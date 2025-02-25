from flask import Flask, request, jsonify
import requests
import spacy

app = Flask(__name__)

# Load the NLP model (could use OpenAI GPT, spaCy, or Rasa)
nlp = spacy.load("en_core_web_sm")

# Simulation of notification APIs (replace with real credentials)
WHATSAPP_API = "https://api.whatsapp.com/send"
SLACK_API = "https://slack.com/api/chat.postMessage"
TEAMS_API = "https://graph.microsoft.com/v1.0/me/sendMail"
EMAIL_API = "https://api.sendgrid.com/v3/mail/send"

# Configuration of AI APIs with failover
OPENAI_API = "https://api.openai.com/v1/chat/completions"
OPENROUTER_API = "https://openrouter.ai/api/chat/completions"
GROQ_API = "https://api.groq.com/v1/chat/completions"
OLLAMA_LOCAL = "http://localhost:11434/v1/chat/completions"
MISTRAL_LOCAL = "http://localhost:5000/v1/chat/completions"

# Function to check the status of AI APIs
def check_api_status(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False

# Function to select the available AI API
def get_active_ai_api():
    if check_api_status(OPENAI_API):
        return OPENAI_API
    elif check_api_status(OPENROUTER_API):
        return OPENROUTER_API
    elif check_api_status(GROQ_API):
        return GROQ_API
    elif check_api_status(OLLAMA_LOCAL):
        return OLLAMA_LOCAL
    elif check_api_status(MISTRAL_LOCAL):
        return MISTRAL_LOCAL
    else:
        return None

# Function to process text using the available AI
def process_with_ai(text):
    api_url = get_active_ai_api()
    if not api_url:
        return "No AI services available."
    response = requests.post(api_url, json={"prompt": text, "max_tokens": 100})
    return response.json().get("response", "Error in AI response")

# Function to analyze natural language text
def process_text(text):
    doc = nlp(text.lower())
    condition, actions = None, []
    
    # Condition identification (e.g., "if risk > 80%")
    for token in doc:
        if token.text in ["risk", "level", "score"]:
            condition = "risk > 80%"
    
    # Action identification (e.g., "send alert via WhatsApp and Slack")
    for token in doc:
        if "whatsapp" in token.text:
            actions.append("whatsapp")
        elif "slack" in token.text:
            actions.append("slack")
        elif "teams" in token.text:
            actions.append("teams")
        elif "email" in token.text:
            actions.append("email")
    
    return condition, actions

# Function to send notifications
def send_notification(service, message):
    if service == "whatsapp":
        requests.post(WHATSAPP_API, json={"message": message})
    elif service == "slack":
        requests.post(SLACK_API, json={"text": message})
    elif service == "teams":
        requests.post(TEAMS_API, json={"content": message})
    elif service == "email":
        requests.post(EMAIL_API, json={"subject": "Risk Alert", "content": message})
    return f"Notification sent via {service}"

# Endpoint to receive natural language instructions
@app.route("/configure", methods=["POST"])
def configure():
    data = request.json
    text = data.get("text")
    
    condition, actions = process_text(text)
    
    if condition and actions:
        message = f"Alert: {condition}"
        responses = [send_notification(a, message) for a in actions]
        return jsonify({"message": "Rule configured", "actions": responses})
    else:
        return jsonify({"error": "Instruction not understood."}), 400

# Endpoint to process queries with AI
@app.route("/ai", methods=["POST"])
def ai_endpoint():
    data = request.json
    text = data.get("text")
    ai_response = process_with_ai(text)
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    app.run(debug=True)
