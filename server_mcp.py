import os.path
import datetime
import pytz
from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = pytz.timezone('Atlantic/Canary')

def get_calendar_service():
    creds = None
    token_json_str = os.environ.get('GOOGLE_TOKEN_JSON')
    if token_json_str:
        creds = Credentials.from_authorized_user_info(json.loads(token_json_str), SCOPES)
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
            "tools": [{
                "name": "gestisci_appuntamento_semplice",
                "description": "Controlla la disponibilità per un orario e fissa un appuntamento di test.",
                "parameters": [
                    {"name": "time", "type": "string", "description": "L'orario richiesto, es. '16:00'"}
                ]
            }]
        }
    else:
        service = get_calendar_service()
        if not service:
            return jsonify({"text": "Errore: non riesco a connettermi al calendario."})

        tool_chiamato = dati_ricevuti.get('tool')
        params = dati_ricevuti.get('params', {})

        if tool_chiamato == 'gestisci_appuntamento_semplice':
            try:
                orario_richiesto_str = params.get('time')
                if not orario_richiesto_str:
                    return jsonify({"text": "Per favore, fornisci un orario."})

                giorno_target = datetime.date.today()
                ora = int(orario_richiesto_str.split(':')[0])
                
                naive_dt = datetime.datetime.combine(giorno_target, datetime.time(hour=ora, minute=0))
                aware_dt_start = TIMEZONE.localize(naive_dt)
                aware_dt_end = aware_dt_start + datetime.timedelta(hours=1)
                
                events_result = service.events().list(
                    calendarId='primary', timeMin=aware_dt_start.isoformat(), timeMax=aware_dt_end.isoformat(),
                    maxResults=1, singleEvents=True
                ).execute()
                events = events_result.get('items', [])

                if not events:
                    event = {
                        'summary': 'Appuntamento di Test Semplificato',
                        'start': {'dateTime': aware_dt_start.isoformat(), 'timeZone': 'Atlantic/Canary'},
                        'end': {'dateTime': aware_dt_end.isoformat(), 'timeZone': 'Atlantic/Canary'},
                    }
                    created_event = service.events().insert(calendarId='primary', body=event).execute()
                    print(f"Evento creato: {created_event.get('htmlLink')}")
                    risposta_per_ai = {"text": "Perfetto, test superato! Ho fissato un appuntamento di prova."}
                else:
                    risposta_per_ai = {"text": "Mi dispiace, per quell'ora risulta già un appuntamento."}
            except Exception as e:
                print(f"Errore: {e}")
                risposta_per_ai = {"text": "Scusi, ho avuto un problema durante il test."}
    
    print(f"--- Invio risposta: ---\n{risposta_per_ai}")
    return jsonify(risposta_per_ai)
