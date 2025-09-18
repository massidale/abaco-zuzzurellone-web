
import random
import time
from flask import Flask, render_template, request, jsonify
from game_logic import AbacoGame
from abaco_data import carica_vocabolario, carica_parole_da_indovinare

app = Flask(__name__)

# Caricamento dati
try:
    vocabolario = carica_vocabolario('data/660000_parole_italiane.txt')
    parole_da_indovinare = carica_parole_da_indovinare('data/1000_parole_italiane_comuni.txt')
    parola_segreta = random.choice(parole_da_indovinare)
    
    game = AbacoGame(parola_segreta, vocabolario)
    start_time = time.time()
    print(f"Parola segreta per la sessione: {parola_segreta}")

except FileNotFoundError as e:
    print(f"Errore: {e}")
    print("Assicurati che i file del dizionario si trovino nella cartella 'data'.")
    exit()


@app.route('/')
def index():
    """Renderizza la pagina principale del gioco.""" 
    global start_time
    start_time = time.time() # Reset timer on page load/new game
    stato_iniziale = {
        'parola_minima': game.parola_minima,
        'parola_massima': game.parola_massima,
        'tentativi_rimasti': game.tentativi_rimasti,
        'numero_tentativi': game.numero_tentativi,
        'game_over': game.game_over,
        'elapsed_time': 0
    }
    return render_template('index.html', stato=stato_iniziale)

@app.route('/guess', methods=['POST'])
def guess():
    """Gestisce il tentativo dell'utente."""
    if game.game_over:
        return jsonify({'error': 'La partita è terminata.'}), 400

    data = request.get_json()
    parola_proposta = data.get('parola')

    if not parola_proposta:
        return jsonify({'error': 'Nessuna parola fornita.'}), 400

    risultato = game.processa_tentativo(parola_proposta, 'Player 1')
    
    elapsed_time = time.time() - start_time

    stato_partita = {
        'risultato': risultato,
        'parola_minima': game.parola_minima,
        'parola_massima': game.parola_massima,
        'tentativi_rimasti': game.tentativi_rimasti,
        'numero_tentativi': game.numero_tentativi,
        'game_over': game.game_over,
        'vincitore': game.vincitore,
        'elapsed_time': elapsed_time
    }

    if game.vincitore:
        minutes, seconds = divmod(elapsed_time, 60)
        if minutes > 0:
            tempo_impiegato = f"{int(minutes)} minuti e {int(seconds)} secondi"
        else:
            tempo_impiegato = f"{int(seconds)} secondi"
        stato_partita['risultato'] = f"{risultato}<br>Tempo: {tempo_impiegato}<br>Tentativi: {game.numero_tentativi}"
    
    return jsonify(stato_partita)

@app.route('/restart', methods=['POST'])
def restart():
    """Resetta il gioco con una nuova parola."""
    global game, start_time
    try:
        parola_segreta = random.choice(parole_da_indovinare)
        game = AbacoGame(parola_segreta, vocabolario)
        start_time = time.time()
        print(f"Nuova partita iniziata. Nuova parola segreta: {parola_segreta}")
        
        stato_iniziale = {
            'parola_minima': game.parola_minima,
            'parola_massima': game.parola_massima,
            'tentativi_rimasti': game.tentativi_rimasti,
            'numero_tentativi': game.numero_tentativi,
            'game_over': game.game_over,
            'elapsed_time': 0
        }
        return jsonify(stato_iniziale)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """Restituisce lo stato attuale del gioco, incluso il tempo trascorso."""
    if not game.game_over:
        elapsed_time = time.time() - start_time
        return jsonify({'elapsed_time': elapsed_time, 'game_over': False})
    return jsonify({'elapsed_time': 0, 'game_over': True})

@app.route('/surrender', methods=['POST'])
def surrender():
    """L'utente si arrende e il gioco finisce."""
    if game.game_over:
        return jsonify({'error': 'La partita è già terminata.'}), 400

    game.game_over = True
    return jsonify({
        'risultato': f"Ti sei arreso! La parola segreta era '{game.parola_segreta}'.",
        'parola_segreta': game.parola_segreta,
        'game_over': True
    })

@app.route('/set-custom-word', methods=['POST'])
def set_custom_word():
    """Imposta una parola segreta personalizzata scelta dall'utente."""
    global game, start_time
    try:
        data = request.get_json()
        parola_personalizzata = data.get('parola', '').strip().lower()

        if not parola_personalizzata:
            return jsonify({'error': 'Nessuna parola fornita.'}), 400

        if parola_personalizzata not in vocabolario:
            return jsonify({'error': f'"{parola_personalizzata}" non è una parola valida nel vocabolario.'}), 400

        if parola_personalizzata == 'abaco' or parola_personalizzata == 'zuzzurellone':
            return jsonify({'error': f'La parola non può essere "{parola_personalizzata}" (estremo del range).'}), 400

        game = AbacoGame(parola_personalizzata, vocabolario)
        start_time = time.time()
        print(f"Nuova partita con parola personalizzata: {parola_personalizzata}")

        stato_iniziale = {
            'parola_minima': game.parola_minima,
            'parola_massima': game.parola_massima,
            'tentativi_rimasti': game.tentativi_rimasti,
            'numero_tentativi': game.numero_tentativi,
            'game_over': game.game_over,
            'elapsed_time': 0
        }
        return jsonify(stato_iniziale)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
