import os.path
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
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
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
                    "name": "gestisci_appuntamento",
                    "description": "Controlla la disponibilità e, se c'è posto, crea un nuovo appuntamento. Richiede tutti i dettagli.",
                    "parameters": [
                        {"name": "time", "type": "string", "description": "L'orario dell'appuntamento, es. '16:00'"},
                        {"name": "date", "type": "string", "description": "La data dell'appuntamento, es. 'domani'"},
                        {"name": "summary", "type": "string", "description": "Il titolo dell'evento, es. 'Massaggio Sportivo'"},
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

        if tool_chiamato == 'gestisci_appuntamento':
            try:
                # FASE 1: CONTROLLO DISPONIBILITA' (INTERNO AL SERVER)
                giorno_target = datetime.date.today() # Semplificazione
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
                    # FASE 2: POSTO LIBERO, CREO L'APPUNTAMENTO
                    nome_cliente = params.get('nome', '')
                    cognome_cliente = params.get('cognome', '')
                    telefono_cliente = params.get('telefono', 'Non fornito')
                    descrizione_evento = f"Cliente: {nome_cliente} {cognome_cliente}\nTelefono: {telefono_cliente}"

                    event = {
                        'summary': f"{params.get('summary', 'Appuntamento')} - {nome_cliente} {cognome_cliente}",
                        'description': descrizione_evento,
                        'start': {'dateTime': aware_dt_start.isoformat(), 'timeZone': 'Atlantic/Canary'},
                        'end': {'dateTime': aware_dt_end.isoformat(), 'timeZone': 'Atlantic/Canary'},
                    }

                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    print(f"Evento creato: {created_event.get('htmlLink')}")
                    risposta_per_ai = {"text": "Perfetto, ho controllato e c'era posto. Ho fissato il suo appuntamento in agenda. Grazie e a presto!"}
                else:
                    # POSTO OCCUPATO
                    risposta_per_ai = {"text": "Ho controllato l'agenda. Mi dispiace, ma per quell'ora risulta già un appuntamento. Desidera provare un altro orario?"}
            except Exception as e:
                print(f"Errore: {e}")
                risposta_per_ai = {"text": "Scusi, ho avuto un problema. Può ripetere i dati per la prenotazione?"}
    
    print(f"--- Invio risposta: ---\n{risposta_per_ai}")
    return jsonify(risposta_per_ai)
