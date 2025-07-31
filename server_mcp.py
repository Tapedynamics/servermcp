from flask import Flask, request, jsonify

app = Flask(__name__)

# Aggiungiamo una rotta principale per vedere se il server è vivo
@app.route('/')
def index():
    return "Server di test è attivo e funzionante!"

# La nostra rotta per l'AI
@app.route('/handle_request', methods=['POST'])
def handle_request():
    print("--- Richiesta di test a /handle_request ricevuta correttamente! ---")

    dati_ricevuti = request.json or {} # Legge i dati per evitare errori
    print(f"Dati: {dati_ricevuti}")

    return jsonify({"text": "Il server di test ha risposto con successo!"})

# Non abbiamo più bisogno della parte if __name__ == '__main__':
# perché gunicorn non la usa. La lasciamo pulita così.
