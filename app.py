import random
import time
import secrets
from flask import Flask, render_template, request, jsonify, session
from game_logic import AbacoGame
from abaco_data import carica_vocabolario, carica_parole_da_indovinare

app = Flask(__name__)
# Chiave segreta per le sessioni (necessaria per sicurezza)
app.secret_key = secrets.token_hex(32)

# Caricamento dati (questi possono rimanere globali perché sono solo dati di lettura)
try:
    vocabolario = carica_vocabolario('data/660000_parole_italiane.txt')
    parole_da_indovinare = carica_parole_da_indovinare('data/1000_parole_italiane_comuni.txt')
    print(f"Vocabolario caricato: {len(vocabolario)} parole")
    print(f"Parole da indovinare: {len(parole_da_indovinare)} parole")

except FileNotFoundError as e:
    print(f"Errore: {e}")
    print("Assicurati che i file del dizionario si trovino nella cartella 'data'.")
    exit()

def get_game():
    """Ottiene o crea una nuova istanza di gioco per la sessione corrente."""
    if 'game_id' not in session or 'game_data' not in session:
        # Nuova partita
        parola_segreta = random.choice(parole_da_indovinare)
        game = AbacoGame(parola_segreta, vocabolario)
        session['game_id'] = secrets.token_hex(16)
        session['game_data'] = {
            'parola_segreta': parola_segreta,
            'parola_minima': game.parola_minima,
            'parola_massima': game.parola_massima,
            'numero_tentativi': game.numero_tentativi,
            'game_over': game.game_over,
            'vincitore': game.vincitore,
            'start_time': time.time()
        }
        print(f"Nuova partita per sessione {session['game_id']}: {parola_segreta}")
        return game

    # Ricostruisce il gioco dalla sessione
    data = session['game_data']
    game = AbacoGame(data['parola_segreta'], vocabolario)
    game.parola_minima = data['parola_minima']
    game.parola_massima = data['parola_massima']
    game.numero_tentativi = data['numero_tentativi']
    game.game_over = data['game_over']
    game.vincitore = data['vincitore']
    return game

def save_game(game):
    """Salva lo stato del gioco nella sessione."""
    session['game_data'] = {
        'parola_segreta': game.parola_segreta,
        'parola_minima': game.parola_minima,
        'parola_massima': game.parola_massima,
        'numero_tentativi': game.numero_tentativi,
        'game_over': game.game_over,
        'vincitore': game.vincitore,
        'start_time': session.get('game_data', {}).get('start_time', time.time())
    }

@app.route('/')
def index():
    """Renderizza la pagina principale del gioco."""
    game = get_game()
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
    game = get_game()

    if game.game_over:
        return jsonify({'error': 'La partita è terminata.'}), 400

    data = request.get_json()
    parola_proposta = data.get('parola')

    if not parola_proposta:
        return jsonify({'error': 'Nessuna parola fornita.'}), 400

    risultato = game.processa_tentativo(parola_proposta, 'Player 1')
    save_game(game)

    start_time = session['game_data']['start_time']
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
    try:
        # Cancella la sessione corrente per forzare una nuova partita
        session.clear()
        game = get_game()  # Questo creerà una nuova partita

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
    game = get_game()
    if not game.game_over:
        start_time = session.get('game_data', {}).get('start_time', time.time())
        elapsed_time = time.time() - start_time
        return jsonify({'elapsed_time': elapsed_time, 'game_over': False})
    return jsonify({'elapsed_time': 0, 'game_over': True})

@app.route('/hint', methods=['POST'])
def hint():
    """Fornisce un indizio basato sul prefisso comune tra i due estremi."""
    game = get_game()
    if game.game_over:
        return jsonify({'error': 'La partita è già terminata.'}), 400

    # Prendi i due estremi attuali
    min_word = game.parola_minima
    max_word = game.parola_massima
    parola_segreta = game.parola_segreta

    # Trova il prefisso comune tra i due estremi
    lcp_len = 0
    while (lcp_len < len(min_word) and
           lcp_len < len(max_word) and
           min_word[lcp_len] == max_word[lcp_len]):
        lcp_len += 1

    # Determina quale lettera rivelare basandosi sul prefisso comune
    if lcp_len < len(parola_segreta):
        lettera_da_rivelare = parola_segreta[lcp_len]
        posizione = lcp_len + 1

        # Aggiorna il range basandosi sulla lettera rivelata
        nuovo_prefisso = parola_segreta[:lcp_len + 1]

        # Trova le parole nel vocabolario che iniziano con questo prefisso
        parole_con_prefisso = [w for w in vocabolario if w.startswith(nuovo_prefisso)]

        if parole_con_prefisso:
            # Trova la parola minima e massima che inizia con questo prefisso
            # e che è ancora nel range corrente
            nuova_minima = max(game.parola_minima, min(parole_con_prefisso))
            nuova_massima = min(game.parola_massima, max(parole_con_prefisso))

            # Aggiorna il range del gioco
            game.parola_minima = nuova_minima
            game.parola_massima = nuova_massima
            save_game(game)
    else:
        return jsonify({'error': 'Non ci sono più lettere da rivelare!'}), 400

    # Formatta il messaggio senza apici e con lettera in bold (HTML)
    messaggio = f"La {posizione}ª lettera è: &nbsp;&nbsp;<strong>{lettera_da_rivelare}</strong>"

    return jsonify({
        'messaggio': messaggio,
        'prefisso_rivelato': nuovo_prefisso,
        'parola_minima': game.parola_minima,
        'parola_massima': game.parola_massima,
        'numero_tentativi': game.numero_tentativi
    })

@app.route('/surrender', methods=['POST'])
def surrender():
    """L'utente si arrende e il gioco finisce."""
    game = get_game()
    if game.game_over:
        return jsonify({'error': 'La partita è già terminata.'}), 400

    game.game_over = True
    save_game(game)
    return jsonify({
        'risultato': f"Ti sei arreso! La parola segreta era '{game.parola_segreta}'.",
        'parola_segreta': game.parola_segreta,
        'game_over': True
    })

@app.route('/get-alphabet-prefixes', methods=['POST'])
def get_alphabet_prefixes():
    """Genera i prefissi filtrati per l'alfabeto ausiliario."""
    try:
        data = request.get_json()
        min_word = data.get('min_word', '').lower()
        max_word = data.get('max_word', '').lower()

        if not min_word or not max_word:
            return jsonify({'prefixes': []})

        # Genera prefissi intelligenti basati sul vocabolario
        prefixes = genera_prefissi_filtrati(min_word, max_word, vocabolario)

        return jsonify({'prefixes': prefixes})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def genera_prefissi_filtrati(min_word, max_word, vocab):
    """Genera prefissi con la logica originale ma filtrati per esistenza nel vocabolario."""

    # Se sono le parole iniziali/finali, mostra l'alfabeto completo
    if min_word == 'abaco' and max_word == 'zuzzurellone':
        return [f'{letter}...' for letter in 'abcdefghijklmnopqrstuvwxyz']

    # Prima genera i prefissi candidati con la logica originale
    candidate_prefixes = []

    # Trova il prefisso comune più lungo
    lcp_len = 0
    while lcp_len < len(min_word) and lcp_len < len(max_word) and min_word[lcp_len] == max_word[lcp_len]:
        lcp_len += 1

    if lcp_len > 0:
        # Ha prefisso comune
        common_prefix = min_word[:lcp_len]

        if len(min_word) == lcp_len:
            # min_word è prefisso di max_word
            for c in range(ord('a'), ord(max_word[lcp_len])):
                candidate_prefixes.append(min_word + chr(c))
        else:
            start_char = ord(min_word[lcp_len])
            end_char = ord(max_word[lcp_len])

            if end_char == start_char + 1:
                # Caratteri adiacenti dopo prefisso comune
                # Prima variante
                prefix1 = common_prefix + chr(start_char)
                start_char2 = ord(min_word[lcp_len + 1]) if len(min_word) > lcp_len + 1 else ord('a')
                for c2 in range(start_char2, ord('z') + 1):
                    candidate_prefixes.append(prefix1 + chr(c2))

                # Seconda variante
                prefix2 = common_prefix + chr(end_char)
                end_char2 = ord(max_word[lcp_len + 1]) if len(max_word) > lcp_len + 1 else ord('z')
                for c2 in range(ord('a'), end_char2 + 1):
                    candidate_prefixes.append(prefix2 + chr(c2))
            else:
                # Caratteri non adiacenti
                for c in range(start_char, end_char + 1):
                    candidate_prefixes.append(common_prefix + chr(c))
    else:
        # Nessun prefisso comune
        start_char = ord(min_word[0])
        end_char = ord(max_word[0])

        if end_char == start_char + 1:
            # Lettere adiacenti (es. e-f)
            # Prima lettera
            first_letter = chr(start_char)
            start_second = ord(min_word[1]) if len(min_word) > 1 else ord('a')
            for c2 in range(start_second, ord('z') + 1):
                candidate_prefixes.append(first_letter + chr(c2))

            # Seconda lettera
            second_letter = chr(end_char)
            end_second = ord(max_word[1]) if len(max_word) > 1 else ord('z')
            for c2 in range(ord('a'), end_second + 1):
                candidate_prefixes.append(second_letter + chr(c2))
        else:
            # Lettere non adiacenti
            for c in range(start_char, end_char + 1):
                candidate_prefixes.append(chr(c))

    # Se i prefissi sono di una sola lettera, non filtrare (sono sempre validi)
    if candidate_prefixes and len(candidate_prefixes[0]) == 1:
        valid_prefixes = candidate_prefixes
    else:
        # Ora filtra: mantieni solo i prefissi che hanno almeno una parola nel vocabolario
        # Per efficienza, crea un set delle parole nel range
        words_in_range = {w for w in vocab if min_word <= w <= max_word}

        # Funzione helper per filtrare i prefissi
        def filter_prefixes(prefixes_to_check):
            valid = []
            for prefix in sorted(set(prefixes_to_check)):
                # Controlla se esiste almeno una parola che inizia con questo prefisso
                has_word = any(word.startswith(prefix) for word in words_in_range)
                if has_word:
                    valid.append(prefix)
            return valid

        # Prima prova con i prefissi candidati originali
        valid_prefixes = filter_prefixes(candidate_prefixes)

    # Se ci sono solo 2 o meno prefissi validi (tipicamente gli estremi),
    # espandi automaticamente di una lettera
    current_prefixes = valid_prefixes if valid_prefixes else candidate_prefixes
    expansion_level = 0
    max_expansions = 2  # Massimo 2 livelli di espansione (es. da 2 a 3 a 4 lettere)

    # Solo se non siamo già a prefissi di una lettera
    if not (valid_prefixes and len(valid_prefixes[0]) == 1):
        while len(valid_prefixes) <= 2 and expansion_level < max_expansions:
            longer_candidates = []
            for prefix in set(current_prefixes):
                for c in 'abcdefghijklmnopqrstuvwxyz':
                    longer_candidates.append(prefix + c)

            # Filtra i nuovi prefissi più lunghi
            if 'filter_prefixes' in locals():
                valid_prefixes = filter_prefixes(longer_candidates)
            else:
                # Se siamo arrivati qui da prefissi di 1 lettera, non filtrare
                valid_prefixes = longer_candidates

            # Se abbiamo trovato abbastanza prefissi o siamo al limite, fermati
            if len(valid_prefixes) > 2:
                break

            current_prefixes = longer_candidates if longer_candidates else current_prefixes
            expansion_level += 1

    # Formatta i prefissi per la visualizzazione
    return [f'{p}...' for p in valid_prefixes]

@app.route('/set-custom-word', methods=['POST'])
def set_custom_word():
    """Imposta una parola segreta personalizzata scelta dall'utente."""
    try:
        data = request.get_json()
        parola_personalizzata = data.get('parola', '').strip().lower()

        if not parola_personalizzata:
            return jsonify({'error': 'Nessuna parola fornita.'}), 400

        if parola_personalizzata not in vocabolario:
            return jsonify({'error': f'"{parola_personalizzata}" non è una parola valida nel vocabolario.'}), 400

        # Crea una nuova partita con la parola personalizzata
        session.clear()
        game = AbacoGame(parola_personalizzata, vocabolario)
        session['game_id'] = secrets.token_hex(16)
        session['game_data'] = {
            'parola_segreta': parola_personalizzata,
            'parola_minima': game.parola_minima,
            'parola_massima': game.parola_massima,
            'numero_tentativi': game.numero_tentativi,
            'game_over': game.game_over,
            'vincitore': game.vincitore,
            'start_time': time.time()
        }
        print(f"Nuova partita personalizzata per sessione {session['game_id']}: {parola_personalizzata}")

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