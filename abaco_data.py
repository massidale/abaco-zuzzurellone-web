"""
Modulo per la gestione dei dati, come il caricamento del vocabolario.
"""
import os
import json
from typing import Set, List

ARTICOLI = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "un'"
}

def carica_parole_da_indovinare(file_path: str) -> List[str]:
    """
    Carica un elenco di parole da un file di testo, una parola per riga,
    e le filtra per rimuovere articoli e parole troppo corte.

    Args:
        file_path: Il percorso del file di testo.

    Returns:
        Una lista di parole filtrate.
        
    Raises:
        FileNotFoundError: Se il file non viene trovato.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File delle parole da indovinare non trovato in: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        parole = {line.strip().lower() for line in f if line.strip()}
    
    # Filtra gli articoli e le parole con 1 o 2 caratteri
    parole_filtrate = [
        parola for parola in parole 
        if parola not in ARTICOLI and len(parola) > 2
    ]
    return parole_filtrate

def carica_vocabolario(file_path: str) -> Set[str]:
    """
    Carica un elenco di parole da un file di testo, una parola per riga.

    Args:
        file_path: Il percorso del file di testo.

    Returns:
        Un set di parole in minuscolo.
        
    Raises:
        FileNotFoundError: Se il file non viene trovato.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File del vocabolario non trovato in: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Rimuove spazi bianchi e converte in minuscolo
        parole = {line.strip().lower() for line in f if line.strip()}
    return parole

def salva_punteggio(giocatori: List[dict]):
    """
    Salva i punteggi dei giocatori (funzionalità da implementare).
    
    Args:
        giocatori: Una lista di dizionari rappresentanti i giocatori e i loro punteggi.
    """
    # TODO: Implementare il salvataggio su file (es. JSON o CSV)
    print("\n(Funzione di salvataggio punteggio non ancora implementata.)")