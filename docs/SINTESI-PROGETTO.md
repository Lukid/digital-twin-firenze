# Gemello digitale di Firenze Novoli: sintesi

Aggiornato al 22 ottobre 2026.

## Cos'è

Un prototipo di gemello digitale di un'area di Firenze: Novoli - Firenze Nova, circa 2 km² nel quartiere 5. Ricostruisce in 3D edifici, alberi, strade e percorsi pedonali, e ci fa sopra dei calcoli: quanto si cammina, quanta ombra c'è sui percorsi, cosa cambia con un intervento.

È costruito solo con open data già pubblicati da Comune di Firenze, Regione Toscana e altri enti, tutti con una licenza che ne permette il riuso.

Ha due interfacce che leggono gli stessi risultati:

- una scena 3D nel browser, con livelli, posizione del sole, analisi e interventi;
- un servizio di interrogazione per assistenti basati su modelli linguistici (protocollo aperto MCP): si fa una domanda in italiano e l'assistente risponde con numeri calcolati, fonti e limiti.

## A cosa serve

Mostrare a un ente pubblico cosa si ottiene combinando i dati aperti che già esistono con calcoli riproducibili, su una domanda concreta di pianificazione.

Il primo caso d'uso è il caldo estivo, da discutere con un ufficio del Comune di Firenze.

## Il caso d'uso: il caldo d'estate

Domande a cui risponde oggi:

- quanti residenti raggiungono a piedi un rifugio climatico entro 5, 10 o 15 minuti;
- quanti ci arrivano camminando soprattutto all'ombra;
- quali percorsi verso scuole, fermate e rifugi sono più esposti al sole alle 14 di luglio;
- quanta ombra in più dà un filare di alberi o una pensilina, e quanto costa.

Alcuni risultati (non ancora verificati sul posto):

- 43,6% dei residenti stimati è entro 10 minuti a piedi dal rifugio climatico più vicino (39,1% dei civici).
- Solo circa 33 residenti stimati (0,2%) ci arrivano entro 10 minuti con almeno metà del percorso in ombra, alle 14 del 15 luglio. Camminando sempre sul lato più in ombra della strada, al massimo 849 (6,1%).
- Sul percorso dalla fermata del tram San Donato - Università al Polo universitario, un filare di 7 platani toglie circa 0,4 minuti di sole a mezzogiorno di luglio. Costo stimato dal prezzario regionale 2026: 3.835 euro, cioè 38 m² d'ombra per mille euro.
- Una pensilina alla fermata dell'autobus porta l'area di attesa dallo 0% al 40% d'ombra a mezzogiorno di luglio.

## Principi

1. Solo dati con licenza di riuso verificata. Ogni fonte ha una scheda con licenza, data del dato e limiti.
2. Ogni numero è riproducibile: stessa domanda e stessi dati danno lo stesso calcolo, con un identificativo che lo richiama.
3. Ogni risultato dichiara fonti, parametri e limiti. Se un calcolo non esiste, il sistema dice "non lo so" e non stima.

Il valore sta nel calcolo e nella sua tracciabilità, non nell'interfaccia.

## Cosa non fa

- Non calcola temperature né comfort termico: solo ombra geometrica e minuti al sole.
- Non conta persone: usa i civici e una stima dei residenti dal censimento 2011.
- Non valuta la fattibilità degli interventi (sottoservizi, proprietà, codice della strada).
- Nessun risultato è ancora validato sul posto.

## Stato

- Fatto: dati, rete pedonale, edifici e alberi, accessibilità, ombre, scenari, scena 3D, servizio per assistenti, dieci domande di prova sul caso caldo, documento tecnico.
- Pronto ma non installato: servizio per assistenti raggiungibile da remoto in sola lettura, sulla macchina di prova.
- In attesa: incontro con l'ufficio del Comune; dal Comune servono il costo del piano delle 72 pensiline, la conferma della voce di piantagione e gli orari estivi dei rifugi.
- Prossima verifica sul posto: percorso R01, sabato 12 dicembre 2026.

## Prossimi passi

1. Installare il servizio remoto e farlo provare a un collega senza assistenza.
2. Primo incontro con l'ufficio del Comune: le dieci domande del caso caldo come bozza da riscrivere con le loro parole.
3. Verifica sul posto del 12 dicembre: ingressi, linea del marciapiede, ombra osservata.
4. Gennaio 2027: demo e documento all'ufficio, candidatura come storia di riuso dei dati aperti.

Fuori fino a febbraio: allagamenti, una seconda area, rilievi da drone.
