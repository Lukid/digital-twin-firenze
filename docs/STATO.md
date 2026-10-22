# Stato del progetto

Aggiornato al 22 ottobre 2026.

## In una riga

Prototipo completo su Firenze Novoli - Firenze Nova: accessibilità pedonale, ombra sui percorsi, scenari di intervento con costi, scena 3D e servizio per assistenti (MCP). Il caso d'uso è il caldo estivo. Nessun risultato è validato sul posto.

## Fatto

| Modulo | Dove | Controllo |
|---|---|---|
| Contratti a più aree | `contracts/` (ADR-F02.md) | `pipeline/.venv/bin/python contracts/validate.py` |
| Acquisizione e baseline, 14 fonti nella baseline | `pipeline/` (REPORT-F03.md) | `pipeline/.venv/bin/python pipeline/validate_records.py` |
| Rete e ingressi | `network/` (REPORT-F04.md) | `pipeline/.venv/bin/python network/test_rete_firenze.py` |
| Edifici e verde | `geometry/` (REPORT-F05.md) | `pipeline/.venv/bin/python geometry/test_geometrie_firenze.py` |
| Accessibilità | `analysis/` (REPORT-F06.md) | `bash analysis/run.sh` |
| Ombre | `shadow/` (REPORT-F07.md) | `pipeline/.venv/bin/python shadow/test_ombre.py` (90 s) |
| Scenari | `scenarios/` (REPORT-F08.md) | `bash scenarios/run.sh` (15 min senza cache) |
| Scena 3D | `scene/firenze_novoli/` (ADR-F09.md) | `pipeline/.venv/bin/python scene/firenze_novoli/test_build.py` e verifica nel browser |
| Servizio e MCP `dt-firenze` | `service/` (REPORT-F10.md) | `service/.venv/bin/python service/test_service.py` |
| Verifica in linguaggio naturale | `nl/firenze_novoli/` (REPORT.md) | `service/.venv/bin/python nl/firenze_novoli/test_nl.py` (30 s) |

Vedere la scena: `cd scene/firenze_novoli && python3 -m http.server 8765`, poi http://localhost:8765/ (funziona senza rete; gli edifici vanno rigenerati in locale, vedi il README).

## Risultati principali (non validati sul posto)

- Accessibilità a 1,2 m/s, quota dei 3.296 civici entro 10 minuti: Polo delle Scienze Sociali 28% (54% entro 15), scuola Vamba 39%, fermate T2 San Donato - Università 24%, Regione Toscana 30%, Torre degli Agli 39%.
- Rifugi climatici: 39,1% dei civici e 43,6% dei residenti stimati entro 10 minuti dal più vicino.
- Arrivo al rifugio all'ombra (14 del 15 luglio, almeno metà del percorso in ombra): circa 33 residenti stimati (0,2%) entro 10 minuti sull'asse della strada; al massimo 849 (6,1%) camminando sul lato più in ombra. Senza soglia: percorso in ombra in media per il 21%, 4,5 minuti al sole in mediana.
- Ombra fra le 12:30 e le 13:30 su R01 (fermata San Donato - Università → Polo, 429 m): 30% a luglio, 72% a settembre. Alberi e vegetazione pesano meno di 2 punti.
- Filare S1 su R01: -0,36 minuti di sole a mezzogiorno di luglio; costo 3.834,95 euro, 38,07 m² d'ombra per mille euro.
- Pensiline S2 e S5: area di attesa dallo 0% al 40% d'ombra a mezzogiorno di luglio; nessun prezzo pubblico utilizzabile.

## Limiti principali

- Ombra calcolata sull'asse della strada. L'ombra sui due lati è un prototipo e nelle risposte vale solo come limite superiore. La distanza del lato viene dal marciapiede mappato in OSM; dove manca, dal bordo delle aree stradali del Comune meno 1,7 m; altrimenti è un valore dichiarato di 3 m.
- Ombra geometrica binaria; vegetazione laser come volume pieno (limite superiore); nessuna temperatura né comfort.
- Rete solo da OSM; ingressi del Polo e dei rifugi = civici del Comune, non verificati; orari dei rifugi ignoti.
- Civici come punti d'indirizzo; residenti 2011 ripartiti in modo uniforme sui civici della sezione.
- Edifici: impronte 2011 e altezze dal laser 2023, portici ignoti, datum verticale non confermato.
- "Soprattutto all'ombra" dipende molto dalla soglia del 50%, scelta da noi (da 29 a 405 residenti fra 60% e 40%).
- Costo solo per i filari: albero da vivaio contro ombra a maturità, scavo e manutenzione esclusi.
- Feed GTFS dei bus valido a finestre di tre settimane: i calcoli usano solo le posizioni delle fermate.

## Decisioni

- D12-D14: pilota a Firenze, riquadro FP; destinazioni Polo, T2, Vamba; rete con margine di 700 m solo da OSM; chioma laser senza albero censito inclusa nelle ombre.
- D15: solo fonti con licenza di riuso; Pisa accantonata.
- D16, D17, D20: filare S1 con la regola delle aree pedonali del Comune; pensilina S2 alla fermata Guidoni Barsanti; fermata T2 San Donato - Università fra le destinazioni.
- D19: ingressi del Polo = 7 civici, uno per edificio; per ogni origine vince il più vicino.
- D21, D24: dati ARPAT dall'archivio pubblico con le licenze dichiarate; protezione civile dal Comune (CC BY 4.0), non da ripubblicazioni senza licenza.
- D22: niente webcam (nessuna fonte riusabile).
- D23: pannello della scena a schede sul modello di Padova.
- D25: caso d'uso principale: caldo estivo (ombra, rifugi climatici, costi degli interventi).
- D32: i 7 rifugi climatici entro 700 m fra le destinazioni.
- D33, D36, D41: costo solo per i filari, indicatore "m² d'ombra per mille euro"; platano orientale 18/20 dal prezzario regionale 2026; voce di piantagione da confermare con il Comune.
- D37, D42, D43: pensiline senza costo nei calcoli; i costi unitari ANAC (CC BY-SA 4.0) solo come riferimento citato.
- D39: coordinate arrotondate prima di scrivere i file, per avere gli stessi byte su macchine diverse.
- D44: scena sul terreno attuale; rifugi e percorsi fuori dal terreno restano in elenco.
- D45, D48: residenti 2011 stimati per civico, sempre accanto alla quota dei civici.
- D49, D53: "soprattutto all'ombra" = almeno il 50% del percorso in ombra alle 14 del 15 luglio, con 40% e 60% accanto e un indicatore senza soglia.
- D54: nessun punteggio unico pesato fra scenari.
- D56, D59, D60, D63, D67: ombra sui due lati della strada accanto all'asse, come limite superiore; distanza dalle aree stradali meno 1,7 m, sotto 1 m si torna ai 3 m dichiarati.
- D50, D68: verifica sul posto di R01 sabato 12 dicembre 2026; lì si ricontrolla anche il margine di 1,7 m.

## Prossimi passi

1. Installare il servizio MCP remoto in sola lettura (`service/INSTALLA-REMOTO.md`).
2. Primo incontro con un ufficio del Comune: dieci domande sul caso caldo da riscrivere con le loro parole. Da chiedere: costo del piano delle 72 pensiline, voce di piantagione, orari estivi dei rifugi.
3. Verifica sul posto di R01 il 12 dicembre 2026: ingressi, linea del marciapiede, ombra osservata.
4. Difetti aperti del servizio emersi dalla verifica in linguaggio naturale: `nl/firenze_novoli/REPORT.md`.

## Regole per chi modifica i motori

- Chi modifica `analysis/accessibilita.py` o `shadow/ombre.py` aggiorna il loro hash in `scenarios/firenze_novoli/baseline.json`, con una nota che riporta l'hash vecchio, e riesegue il confronto degli scenari: se la modifica non deve cambiare i risultati, il confronto deve uscire identico a `confronto.json`; altrimenti va rifatto `scenarios/run.sh`. Senza questo passo `compare_scenarios` rifiuta il confronto (`incompatible_baseline`).
- La cache del servizio si svuota da sola quando cambiano il codice dei motori o i file di dati che leggono. I job_id non cambiano.
- I numeri nei report si cambiano solo rieseguendo il calcolo.
