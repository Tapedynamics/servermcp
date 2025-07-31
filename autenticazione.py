import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Definisce a cosa chiediamo il permesso di accedere (Calendar e Gmail)
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/gmail.send"]

def main():
    creds = None
    # Il file token.json salva le chiavi di accesso e viene creato
    # automaticamente la prima volta che eseguiamo questo script.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # Se non ci sono credenziali valide, facciamo fare il login all'utente.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Usa il file credentials.json che abbiamo scaricato da Google
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salviamo le credenziali (il token) per le esecuzioni future
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    print("Autenticazione completata con successo! Il file 'token.json' e' stato creato.")
    print("Ora puoi chiudere questa finestra.")

if __name__ == "__main__":
    main()