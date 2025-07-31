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
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = pytz.timezone('Atlantic/Canary')

def get_calendar_service():
    creds = None
    token_json_str = os.environ.get('GOOGLE_TOKEN_JSON')
    if token_json_str:
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else: return None
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"Errore connessione servizio: {error}")
        return None

@app.route('/handle_request', methods=['POST'])
def handle_request():
    dati_ricevuti = request.json
    print(f"--- Dati ricevuti: ---\n{dati_ricevuti}")

    method = dati_ricevuti.get('method')
    risposta_per_ai = {}

    if method == 'initialize':
        risposta_per_ai = {
            "tools": [
                {
                    "name": "controlla_disponibilita",
                    "description": "Controlla la disponibilità nel calendario per una data e ora.",
                    "parameters": [
                        {"name": "time", "type": "string", "description": "L'orario richiesto, es. '16:00'"},
                        {"name": "date", "type": "string", "description": "La data richiesta, es. 'domani'"}
                    ]
                },
                {
                    "name": "crea_appuntamento",
                    "description": "Crea un nuovo appuntamento nel calendario.",
                    "parameters": [
                        {"name": "time", "type": "string", "description": "L'orario dell'appuntamento"},
                        {"name": "date", "type": "string", "description": "La data dell'appuntamento"},
                        {"name": "summary", "type": "string", "description": "Il titolo dell'evento"},
                        {"name": "nome", "type": "string", "description": "Il nome del cliente"},
                        {"name": "cognome", "type": "string", "description": "Il cognome del cliente"},
                        {"name": "telefono", "type": "string", "description": "Il numero di telefono del cliente"}
                    ]
                }
            ]
        }
    else:
        service = get_calendar_service()
        if not service:
            return jsonify({"text": "Errore: non riesco a connettermi al calendario."})

        tool_chiamato = dati_ricevuti.get('tool')
        params = dati_ricevuti.get('params', {})

        if tool_chiamato == 'controlla_disponibilita':
            try:
                giorno_target = datetime.date.today()
                # --- CORREZIONE QUI ---
                ora = int(params['time'].split(':')[0]) 
                minuti = int(params['time'].split(':')[1]) if ':' in params['time'] else 0
                
                naive_dt = datetime.datetime.combine(giorno_target, datetime.time(hour=ora, minute=minuti))
                aware_dt_start = TIMEZONE.localize(naive_dt)
                aware_dt_end = aware_dt_start + datetime.timedelta(hours=1)

                events_result = service.events().list(
                    calendarId='primary', timeMin=aware_dt_start.isoformat(), timeMax=aware_dt_end.isoformat(),
                    maxResults=1, singleEvents=True
                ).execute()
                events = events_result.get('items', [])

                if not events:
                    risposta_per_ai = {"text": "Ho controllato l'agenda! Sì, per quell'ora c'è disponibilità. Posso confermare l'appuntamento?"}
                else:
                    risposta_per_ai = {"text": "Ho controllato l'agenda. Mi dispiace, ma per quell'ora risulta già un appuntamento."}
            except Exception as e:
                print(f"Errore: {e}")
                risposta_per_ai = {"text": "Scusi, ho avuto un problema nel leggere l'agenda."}

        elif tool_chiamato == 'crea_appuntamento':
            try:
                giorno_target = datetime.date.today()
                # --- E CORREZIONE QUI ---
                ora = int(params['time'].split(':')[0])
                minuti = int(params['time'].split(':')[1]) if ':' in params['time'] else 0

                aware_dt_start = TIMEZONE.localize(datetime.datetime.combine(giorno_target, datetime.time(hour=ora, minute=minuti)))
                aware_dt_end = aware_dt_start + datetime.timedelta(hours=1)

                nome_cliente = params.get('nome', '')
                cognome_cliente = params.get('cognome', '')
                telefono_cliente = params.get('telefono', 'Non fornito')
                
                descrizione_evento = f"Cliente: {nome_cliente} {cognome_cliente}\nTelefono
