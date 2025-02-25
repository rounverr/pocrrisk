from flask import Flask, request, jsonify
import requests
import spacy

app = Flask(__name__)

# Cargar modelo de NLP (puede usarse OpenAI GPT, spaCy o Rasa)
nlp = spacy.load("en_core_web_sm")

# Simulación de APIs de notificación (reemplazar con credenciales reales)
WHATSAPP_API = "https://api.whatsapp.com/send"
SLACK_API = "https://slack.com/api/chat.postMessage"
TEAMS_API = "https://graph.microsoft.com/v1.0/me/sendMail"
EMAIL_API = "https://api.sendgrid.com/v3/mail/send"

# Configuración de APIs de IA con failover
OPENAI_API = "https://api.openai.com/v1/chat/completions"
OPENROUTER_API = "https://openrouter.ai/api/chat/completions"
GROQ_API = "https://api.groq.com/v1/chat/completions"
OLLAMA_LOCAL = "http://localhost:11434/v1/chat/completions"
MISTRAL_LOCAL = "http://localhost:5000/v1/chat/completions"

# Función para verificar el estado de las APIs de IA
def check_api_status(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False

# Función para seleccionar la API de IA disponible
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

# Función para procesar texto con la IA disponible
def procesar_con_ia(texto):
    api_url = get_active_ai_api()
    if not api_url:
        return "No hay servicios de IA disponibles."
    response = requests.post(api_url, json={"prompt": texto, "max_tokens": 100})
    return response.json().get("response", "Error en la respuesta de IA")

# Función para analizar texto en lenguaje natural
def procesar_texto(texto):
    doc = nlp(texto.lower())
    condiciones, acciones = None, []
    
    # Identificación de condición (ejemplo: "si riesgo > 80%")
    for token in doc:
        if token.text in ["riesgo", "nivel", "score"]:
            condiciones = "riesgo > 80%"
    
    # Identificación de acciones (ejemplo: "enviar alerta por WhatsApp y Slack")
    for token in doc:
        if "whatsapp" in token.text:
            acciones.append("whatsapp")
        elif "slack" in token.text:
            acciones.append("slack")
        elif "teams" in token.text:
            acciones.append("teams")
        elif "email" in token.text:
            acciones.append("email")
    
    return condiciones, acciones

# Función para enviar notificaciones
def enviar_notificacion(servicio, mensaje):
    if servicio == "whatsapp":
        requests.post(WHATSAPP_API, json={"message": mensaje})
    elif servicio == "slack":
        requests.post(SLACK_API, json={"text": mensaje})
    elif servicio == "teams":
        requests.post(TEAMS_API, json={"content": mensaje})
    elif servicio == "email":
        requests.post(EMAIL_API, json={"subject": "Alerta de Riesgo", "content": mensaje})
    return f"Notificación enviada por {servicio}"

# Endpoint para recibir instrucciones en lenguaje natural
@app.route("/configurar", methods=["POST"])
def configurar():
    data = request.json
    texto = data.get("texto")
    
    condiciones, acciones = procesar_texto(texto)
    
    if condiciones and acciones:
        mensaje = f"Alerta: {condiciones}"
        respuestas = [enviar_notificacion(a, mensaje) for a in acciones]
        return jsonify({"mensaje": "Regla configurada", "acciones": respuestas})
    else:
        return jsonify({"error": "No se entendió la instrucción."}), 400

# Endpoint para procesar consultas con IA
@app.route("/ia", methods=["POST"])
def ia_endpoint():
    data = request.json
    texto = data.get("texto")
    respuesta_ia = procesar_con_ia(texto)
    return jsonify({"respuesta": respuesta_ia})

if __name__ == "__main__":
    app.run(debug=True)
