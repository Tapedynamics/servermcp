from flask import Flask, request, jsonify

# Creiamo l'applicazione Flask
app = Flask(__name__)

# Definiamo una rotta principale per testare con il browser
@app.route('/')
def index():
    return "Server di test v2 è attivo!"

# Definiamo la rotta per l'assistente AI
@app.route('/handle_request', methods=['POST'])
def handle_request():
    # Stampiamo un messaggio nei log per confermare che siamo entrati qui
    print("--- Richiesta a /handle_request ricevuta con successo! ---")

    # Leggiamo i dati ricevuti per evitare errori
    dati_ricevuti = request.json or {}
    print(f"Dati ricevuti: {dati_ricevuti}")

    # Mandiamo una risposta di successo
    return jsonify({"text": "Il server v2 ha risposto con successo!"})
