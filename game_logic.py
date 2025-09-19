"""
Modulo contenente la logica principale del gioco Abaco Zuzzurellone.
"""
from typing import Set, Optional

class AbacoGame:
    """
    Gestisce la logica e lo stato di una partita di Abaco Zuzzurellone.

    Attributes:
        parola_segreta (str): La parola che i giocatori devono indovinare.
        vocabolario (Set[str]): Il set di parole valide per il gioco.
        parola_minima (str): L'estremo inferiore corrente dell'intervallo di ricerca.
        parola_massima (str): L'estremo superiore corrente dell'intervallo di ricerca.
        max_tentativi (Optional[int]): Il numero massimo di tentativi permessi.
        tentativi_rimasti (Optional[int]): Il contatore dei tentativi rimasti.
        vincitore (Optional[str]): Il nome del giocatore che ha vinto.
        game_over (bool): Flag che indica se la partita è terminata.
        numero_tentativi (int): Contatore dei tentativi effettuati.
    """

    def __init__(self, parola_segreta: str, vocabolario: Set[str], max_tentativi: Optional[int] = None):
        """
        Inizializza una nuova partita.

        Args:
            parola_segreta: La parola da indovinare.
            vocabolario: Il set di parole valide.
            max_tentativi: Numero massimo di tentativi. Se None, i tentativi sono illimitati.
        
        Raises:
            ValueError: Se la parola segreta non è nel vocabolario.
        """
        if parola_segreta.lower() not in vocabolario:
            raise ValueError("La parola segreta deve essere presente nel vocabolario.")

        self.parola_segreta: str = parola_segreta.lower()
        self.vocabolario: Set[str] = vocabolario
        
        self.parola_minima: str = "abaco"
        self.parola_massima: str = "zuzzurellone"
        
        self.max_tentativi: Optional[int] = max_tentativi
        self.tentativi_rimasti: Optional[int] = max_tentativi
        
        self.vincitore: Optional[str] = None
        self.game_over: bool = False
        self.numero_tentativi: int = 0

    def processa_tentativo(self, parola_proposta: str, nome_giocatore: str) -> str:
        """
        Elabora il tentativo di un giocatore e aggiorna lo stato del gioco.

        Args:
            parola_proposta: La parola proposta dal giocatore.
            nome_giocatore: Il nome del giocatore che ha fatto il tentativo.

        Returns:
            Una stringa che descrive il risultato del tentativo.
        """
        parola = parola_proposta.lower()

        if self.game_over:
            return "La partita è già terminata."

        # 1. Validazione
        if parola not in self.vocabolario:
            return f"'{parola}' non è una parola valida nel vocabolario."

        if not (self.parola_minima <= parola <= self.parola_massima):
            return f"'{parola}' non è compresa tra '{self.parola_minima}' e '{self.parola_massima}' (estremi inclusi)."

        # Incrementa il numero di tentativi solo se la parola è valida e nel range
        self.numero_tentativi += 1

        if self.tentativi_rimasti is not None:
            self.tentativi_rimasti -= 1

        # 2. Controllo corrispondenza
        if parola == self.parola_segreta:
            self.vincitore = nome_giocatore
            self.game_over = True
            return f"Hai indovinato! La parola era '{self.parola_segreta}'. Complimenti!"

        # 3. Aggiornamento intervallo
        if parola < self.parola_segreta:
            self.parola_minima = parola
            risultato = "DOPO. La parola segreta viene dopo."
        else: # parola > self.parola_segreta
            self.parola_massima = parola
            risultato = "PRIMA. La parola segreta viene prima."
            
        # 4. Controllo fine tentativi
        if self.tentativi_rimasti == 0:
            self.game_over = True
            risultato += f"\nAvete esaurito i tentativi! La parola era '{self.parola_segreta}'. L'organizzatore vince."

        return risultato

