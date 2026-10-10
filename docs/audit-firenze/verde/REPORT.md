# F01 Verde: Firenze, riquadri FA e FB

Data: 5 ottobre 2026. Riquadri da docs/audit-firenze/RIQUADRO.json. Dati grezzi in data/raw/fi_audit_20261001/, non versionati.

## 1. Fonti e licenze

- Censimento alberi pubblici del Comune di Firenze (dataset "Alberi"), CC BY 4.0. Dichiarato aggiornato ogni giorno (CKAN: frequenza DAILY, ultima modifica 5/10/2026). Il file usato qui è lo scarico del 1 ottobre (82.235 alberi); l'audit dei cataloghi ne conta 82.225 nello scarico del 5 ottobre.
- Siti alberi da rilievo celerimetrico ("Accessori - Siti Alberi", classe sAlbero), CC BY 4.0, dato del 2014, PointZ, in Monte Mario Italia zona 1. 32.472 punti in città.
- Life Escapos, "Alberature pubbliche": CC BY-NC 4.0, non commerciale. Tolto (D15).
- LiDAR 2023: vedi il report edifici (CC BY 4.0).

## 2. Censimento alberi: conteggi e attributi

| | FA | FB | FA e FB insieme (area unione) |
|---|---|---|---|
| Alberi | 1.614 | 2.469 | 3.468 |
| per ettaro | 9,4 | 14,4 | 13,1 |
| Specie vuote | 0 | 0 | 0 |
| Circonferenza nulla o zero | 20 | 26 | 33 |
| Circonferenza p10-p50-p90 (cm) | 14,1 - 53,4 - 144,4 | 18,8 - 56,5 - 163,3 | 15,7 - 53,4 - 160,0 |

Area in comune di FA e FB: 615 alberi.

- Attributi presenti: ID, CODSITO_ALBERO, QUARTIERE, SPECIE, NOME_COMUNE, CIRCONF_CM. Assenti: altezza, chioma, data di impianto o di rilievo.
- Quartiere: 5 per tutti tranne 1 albero in FB.
- ID è unico. CODSITO_ALBERO si ripete in FA: 1.612 valori distinti su 1.614 alberi.
- Specie più frequenti:
  - FA: Tilia x europaea 197, Fraxinus excelsior 172, Celtis australis 138, Cupressus sempervirens 117, Platanus x acerifolia 72.
  - FB: Tilia x europaea 293, Celtis australis 267, Fraxinus excelsior 253, Cupressus sempervirens 196, Platanus x acerifolia 170.

## 3. Siti alberi da rilievo celerimetrico

- Nei riquadri: 994 punti in FA, 1.748 in FB, 2.244 insieme.
- Attributi: solo un id e la quota Z. Nessuna specie.
- Cosa aggiunge: una quota Z affidabile. Contro il DTM 2023 nel punto: mediana -0,07 m, MAE 0,10 m su 2.244 punti.
- Cosa non aggiunge:
  - Non c'è chiave comune con il censimento: l'id dei siti va da 1 a 32.472, CODSITO_ALBERO da 1 a 136.217, e 0% degli id numerici coincide.
  - L'abbinamento per posizione è scarso. In tutta la città la distanza mediana dal sito più vicino è 22,3 m e solo il 30,1% degli alberi del censimento ha un sito entro 3 m. In FA la mediana è 6,1 m (44,2% entro 3 m), in FB 2,5 m (51,6% entro 3 m).
  - I siti sono meno numerosi del censimento (994 contro 1.614 in FA, 1.748 contro 2.469 in FB) e datati 2014: non lo sostituiscono come elenco, servono come posizione rilevata e quota di una parte degli alberi.

## 4. Life Escapos

Sezione tolta il 10 ottobre 2026 (D15): Life Escapos ha licenza CC BY-NC 4.0 e il progetto usa solo dati riusabili anche a fini commerciali. Nessun valore della fonte resta nei file versionati.

## 5. Altezza chioma da CHM

- CHM = DSM 2023 meno DTM 2023 (0,5 m). Il confronto con le altezze Life Escapos è stato tolto (D15, licenza CC BY-NC 4.0).
- Sul censimento, 3.468 alberi in FA e FB, di cui 3.319 a più di 3 m da un edificio: massimo CHM entro 2 m, p10-p50-p90 = 1,8 - 6,7 - 14,4 m. 357 hanno CHM sotto 2 m (albero tolto o posizione sfalsata). La correlazione tra circonferenza e CHM è 0,042: va letta come limite del metodo, non come risultato, perché con 2 m di raggio nei filari si prendono anche i vicini. L'altezza per albero dal censimento richiede segmentazione delle chiome.

## 6. Giudizio sui riquadri per le ombre

| | FA | FB |
|---|---|---|
| Alberi | 1.614 (9,4 per ettaro) | 2.469 (14,4 per ettaro) |
| UV Regione | 972 | 1.459 |
| Edifici OSM con piani o altezza | 5 | 27 |
| Copertura cassone sull'area UV | 31,5% | 60,0% |
| Sito rilevato entro 3 m dall'albero | 44,2% | 51,6% |
| nDSM meno uv_av, mediana | +0,07 m | +0,63 m |
| UV "in costruzione" nel 2011 | 36 | 1 |

- FB ha più alberi e più edifici, quindi più ombra da calcolare, e un abbinamento migliore con i siti rilevati.
- FA ha l'UV 2011 più datata (36 in costruzione), con un'altezza nDSM più vicina a uv_av.
- La geometria da LiDAR è equivalente: 0% di nodata nell'nDSM di entrambi.
- Scelta rimessa all'utente. In sintesi: FB per più oggetti che fanno ombra, FA per avere un riferimento di chioma già abbinato (con la cautela del punto 5) e per essere il candidato D12.

## 7. Limiti

- Il censimento non ha altezza, chioma né data: l'altezza degli alberi viene dal CHM, con le incertezze del punto 5. Il DSM 2023 è di giugno (foglie), l'ombra invernale va trattata a parte.
- Siti alberi: datati 2014, solo una parte degli alberi, senza specie né chiave comune.
- Chiome senza forma: altezza e larghezza non descrivono la trasparenza.

## File e riproduzione

Script in `script/`, campioni in `campioni/`, checksum in `manifest.json`.

Riprodurre dalla radice del progetto, dopo quello degli edifici (usa DSM, DTM e UV scaricati da lì): `docs/audit-firenze/verde/riproduci.sh` (circa 20 secondi).
