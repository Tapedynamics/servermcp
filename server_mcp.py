# Importa le librerie necessarie da Flask
from flask import Flask, request, jsonify

# Crea l'applicazione server
app = Flask(__name__)

# Definisce la "rotta" o "endpoint" che l'AI chiamerà.
# Risponderà solo a richieste di tipo POST.
@app.route('/handle_request', methods=['POST'])
def handle_request():
    """
    Questa funzione viene eseguita ogni volta che l'AI
    invia una richiesta al nostro server.
    """
    
    # Legge i dati inviati dall'AI e li stampa nel terminale
    dati_ricevuti = request.json
    print("--- Dati ricevuti dall'AI: ---")
    print(dati_ricevuti)

    # --- INIZIO NUOVA LOGICA INTELLIGENTE ---

    # Leggiamo i "parametri" inviati dall'AI. Usiamo .get() per evitare errori se non ci sono.
    params = dati_ricevuti.get('params', {})
    # Cerchiamo un parametro chiamato 'time' che l'AI dovrebbe inviarci
    orario_richiesto = params.get('time') 

    # Prepariamo una variabile per il testo della nostra risposta
    testo_risposta = ""

    # Questa è la nostra finta logica di business per il test:
    # Se il cliente chiede un orario (es. "18:00") e l'ora è maggiore o uguale a 17,
    # allora rispondiamo che siamo al completo. Altrimenti, diamo disponibilità.
    if orario_richiesto:
        try:
            # Estraiamo l'ora e la convertiamo in un numero intero per poterla confrontare
            ora = int(orario_richiesto.split(':')[0])
            if ora >= 17:
                testo_risposta = "Mi dispiace, a quell'ora il centro è al completo. Desidera provare un altro orario?"
            else:
                testo_risposta = "Sì, a quell'ora c'è disponibilità. Posso procedere con la prenotazione?"
        except (ValueError, IndexError):
            # Se l'orario non è in un formato valido, diamo una risposta generica
            testo_risposta = "Non ho capito bene l'orario, può ripetere per favore?"
    else:
        # Se l'AI non ci ha passato un orario, non sappiamo cosa fare e lo diciamo.
        testo_risposta = "Certo, mi dica pure l'orario che preferisce e controllo subito la disponibilità."

    # Creiamo la nostra risposta dinamica
    risposta_per_ai = {
        "text": testo_risposta
    }

    # --- FINE NUOVA LOGICA INTELLIGENTE ---

    # Stampa la risposta che stiamo per inviare, sempre per controllo.
    print("--- Invio questa risposta all'AI: ---")
    print(risposta_per_ai)
    
    # Invia la risposta all'AI in formato JSON
    return jsonify(risposta_per_ai)

# Questa riga avvia il server quando esegui il file.
if __name__ == '__main__':
    # Avvia il server sulla porta 5000
    app.run(port=5000)