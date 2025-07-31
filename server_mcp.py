import os.path
import datetime
from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURAZIONE ---
app = Flask(__name__)
# Definiamo gli ambiti di cui abbiamo bisogno. Per ora solo Calendar.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_calendar_service():
    """
    Questa funzione crea e restituisce un servizio del calendario autenticato.
    Usa i file token.json e credentials.json per farlo.
    """
    creds = None
    # Il file token.json contiene le chiavi di accesso permanenti.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # Se le credenziali non sono valide (es. scadute), le rinfresca.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Questo non dovrebbe accadere su un server. L'autenticazione
            # iniziale va fatta solo una volta in locale con autenticazione.py
            print("Errore: credenziali non valide o mancanti. Eseguire autenticazione.py in locale.")
            return None
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"Si è verificato un errore nella connessione al servizio: {error}")
        return None

@app.route('/handle_request', methods=['POST'])
def handle_request():
    """
    Questa è la funzione principale che gestisce tutte le richieste dall'AI.
    """
    dati_ricevuti = request.json
    print(f"--- Dati ricevuti dall'AI: ---\n{dati_ricevuti}")

    method = dati_ricevuti.get('method')

    # Se la piattaforma chiede di descrivere gli strumenti del server
    if method == 'initialize':
        risposta_per_ai = {
            "tools": [{
                "name": "controlla_disponibilita",
                "description": "Controlla se c'è un appuntamento disponibile nel calendario per una data e un'ora specifiche.",
                "parameters": [
                    {"name": "time", "type": "string", "description": "L'orario richiesto, es. '16:00'"},
                    {"name": "date", "type": "string", "description": "La data richiesta, es. 'oggi', 'domani', o '2025-08-01'"}
                ]
            }]
        }
    # Se è una normale richiesta durante la conversazione
    else:
        params = dati_ricevuti.get('params', {})
        orario_richiesto_str = params.get('time')
        data_richiesta_str = params.get('date')

        # Se non abbiamo l'orario, non possiamo controllare.
        if not orario_richiesto_str:
            risposta_per_ai = {"text": "Certamente, mi dica l'orario che le interessa e controllo subito."}
        else:
            service = get_calendar_service()
            if not service:
                risposta_per_ai = {"text": "Si è verificato un errore interno, non riesco a connettermi all'agenda."}
            else:
                try:
                    # --- LOGICA DI CONTROLLO DEL CALENDARIO ---
                    # Imposta la data di oggi se non specificata
                    if not data_richiesta_str or data_richiesta_str.lower() == 'oggi':
                        giorno_target = datetime.date.today()
                    elif data_richiesta_str.lower() == 'domani':
                        giorno_target = datetime.date.today() + datetime.timedelta(days=1)
                    else:
                        # Qui andrebbe inserita una logica per interpretare altre date
                        giorno_target = datetime.date.today()

                    ora = int(orario_richiesto_str.split(':')[0])
                    minuti = int(orario_richiesto_str.split(':')[1]) if ':' in orario_richiesto_str else 0

                    # Definiamo la finestra di tempo da controllare (es. un'ora)
                    time_min_dt = datetime.datetime.combine(giorno_target, datetime.time(hour=ora, minute=minuti))
                    time_max_dt = time_min_dt + datetime.timedelta(hours=1)
                    
                    # Formattazione per l'API di Google
                    time_min_iso = time_min_dt.isoformat() + 'Z'
                    time_max_iso = time_max_dt.isoformat() + 'Z'
                    
                    print(f"Controllo eventi tra {time_min_iso} e {time_max_iso}...")
                    
                    events_result = service.events().list(
                        calendarId='primary', timeMin=time_min_iso, timeMax=time_max_iso,
                        maxResults=1, singleEvents=True
                    ).execute()
                    events = events_result.get('items', [])

                    if not events:
                        testo_risposta = "Ho controllato l'agenda! Sì, per quell'ora c'è disponibilità. Posso confermare l'appuntamento?"
                    else:
                        testo_risposta = "Ho controllato l'agenda. Mi dispiace, ma per quell'ora risulta già un appuntamento. Desidera un altro orario?"

                    risposta_per_ai = {"text": testo_risposta}

                except Exception as e:
                    print(f"Errore durante il controllo del calendario: {e}")
                    risposta_per_ai = {"text": "Scusi, ho avuto un problema nel leggere l'agenda. Può ripetere l'orario?"}

    print(f"--- Invio questa risposta all'AI: ---\n{risposta_per_ai}")
    return jsonify(risposta_per_ai)

if __name__ == '__main__':
    app.run(port=5000)
