import os
import json
import datetime
import pytz
from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURAZIONE ---
app = Flask(__name__)
# Permesso completo di lettura e scrittura per il calendario
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# Fuso orario corretto per Tenerife, che gestisce l'ora legale
TIMEZONE = pytz.timezone('Atlantic/Canary')

def get_calendar_service():
    """
    Crea e restituisce un servizio del calendario autenticato.
    Usa le credenziali dalla variabile d'ambiente GOOGLE_TOKEN_JSON.
    """
    creds = None
    token_json_str = os.environ.get('GOOGLE_TOKEN_JSON')

    if token_json_str:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("ERRORE: Le credenziali (token) non sono state trovate o non sono valide nelle variabili d'ambiente.")
            return None
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"Si è verificato un errore nella connessione al servizio Google: {error}")
        return None

@app.route('/handle_request', methods=['POST'])
def handle_request():
    """
    Questa è la funzione principale che gestisce tutte le richieste dall'AI.
    """
    dati_ricevuti = request.json
    print(f"--- Dati ricevuti: ---\n{dati_ricevuti}")

    method = dati_ricevuti.get('method')
    risposta_per_ai = {}

    # Se la piattaforma chiede di descrivere gli strumenti del server
    if method == 'initialize':
        risposta_per_ai = {
            "tools": [
                {
                    "name": "controlla_disponibilita",
                    "description": "Controlla se c'è un appuntamento disponibile nel calendario per una data e un'ora specifiche.",
                    "parameters": [
                        {"name": "time", "type": "string", "description": "L'orario richiesto, es. '16:00'"},
                        {"name": "date", "type": "string", "description": "La data richiesta, es. 'oggi', 'domani'"}
                    ]
                },
                {
                    "name": "crea_appuntamento",
                    "description": "Crea un nuovo appuntamento nel calendario con tutti i dettagli del cliente.",
                    "parameters": [
                        {"name": "time", "type": "string", "description": "L'orario dell'appuntamento"},
                        {"name": "date", "type": "string", "description": "La data dell'appuntamento"},
                        {"name": "summary", "type": "string", "description": "Il titolo dell'evento, es. 'Massaggio Sportivo'"},
                        {"name": "nome", "type": "string", "description": "Il nome di battesimo del cliente"},
                        {"name": "cognome", "type": "string", "description": "Il cognome del cliente"},
                        {"name": "telefono", "type": "string", "description": "Il numero di telefono del cliente"}
                    ]
                }
            ]
        }
    # Se è una normale richiesta durante la conversazione
    else:
        service = get_calendar_service()
        if not service:
            return jsonify({"text": "Errore critico: non riesco a connettermi al calendario."})

        tool_chiamato = dati_ricevuti.get('tool')
        params = dati_ricevuti.get('params', {})

        if tool_chiamato == 'controlla_disponibilita':
            try:
                # Logica per interpretare la data (semplificata)
                data_richiesta_str = params.get('date', 'oggi').lower()
                if data_richiesta_str == 'domani':
                    giorno_target = datetime.date.today() + datetime.timedelta(days=1)
                else:
                    giorno_target = datetime.date.today()
                
                ora = int(params['time'].split(':')
