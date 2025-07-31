from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "Server di test v3 è attivo!"

@app.route('/handle_request', methods=['POST'])
def handle_request():
    print("--- Richiesta a /handle_request ricevuta con successo! ---")
    return jsonify({"text": "Il server v3 ha risposto correttamente da /handle_request!"})

# --- NUOVA SEZIONE DI DEBUG ---
# Questa funzione "cattura" tutte le altre richieste non definite sopra.
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(path):
    print(f"--- ATTENZIONE: Richiesta ricevuta per un percorso SCONOSCIUTO: /{path} ---")
    print(f"Metodo della richiesta: {request.method}")
    return jsonify({
        "error": "Percorso non trovato (catturato dal debugger)",
        "percorso_richiesto": f"/{path}",
        "messaggio": "Controlla che l'URL inserito in ElevenLabs sia ESATTAMENTE /handle_request, senza spazi, maiuscole o errori di battitura."
    }), 404
