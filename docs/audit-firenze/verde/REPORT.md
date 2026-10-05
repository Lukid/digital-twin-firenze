# F01 Verde: Firenze, riquadri FA e FB

Data: 5 ottobre 2026. Riquadri da docs/audit-firenze/RIQUADRO.json. Dati grezzi in data/raw/fi_audit_20261001/, non versionati.

## 1. Fonti e licenze

- Censimento alberi pubblici del Comune di Firenze (dataset "Alberi"), CC BY 4.0. Dichiarato aggiornato ogni giorno (CKAN: frequenza DAILY, ultima modifica 5/10/2026). Il file usato qui è lo scarico del 1 ottobre (82.235 alberi); l'audit dei cataloghi ne conta 82.225 nello scarico del 5 ottobre.
- Siti alberi da rilievo celerimetrico ("Accessori - Siti Alberi", classe sAlbero), CC BY 4.0, dato del 2014, PointZ, in Monte Mario Italia zona 1. 32.472 punti in città.
- Life Escapos, "Alberature pubbliche" ("Escapos tree census"), CC BY-NC 4.0: uso non commerciale. Qui solo come verifica. Non ridistribuire. I due file di campioni che ne contengono valori (chm_vs_escapos.csv ed escapos_vs_censimento.csv) portano una nota di licenza nel manifest.json.
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

- 50 alberi, tutti in FA. In FB ce ne sono 14, tutti nell'area in comune con FA.
- Specie: Celtis australis 36, Cupressus sempervirens 7, Quercus ilex 4, Populus nigra 2, Picea abies 1.
- Parametri per albero: dbh_cm, h_m (altezza), crn_w_m (larghezza chioma), can_h_m, canopy_area_m2, lai, biomassa e carbonio (abg_mg, c_mg), assorbimenti di inquinanti (co2, o3, pm10, pm25, no2, so2, co).
- Valori minimo, mediana, massimo: h_m 3,5 - 6,7 - 17,0 m; larghezza chioma 2,2 - 6,3 - 15,2 m; can_h_m 2,6 - 3,7 - 8,2 m; area chioma 3,9 - 31,2 - 181,3 m²; LAI 1,94 - 3,50 - 4,50. Nessun valore nullo.
- can_h_m: il significato non è definito nei metadati (profondità della chioma o altezza di inizio chioma). Il suo rapporto mediano con h_m è 0,585. Non va letto come imposta della chioma.
- Abbinamento con il censimento: cens_id corrisponde all'ID del censimento in 50 casi su 50. Distanza tra i punti: mediana 0,72 m, p90 1,88 m, massimo 3,14 m. Specie uguale 50 su 50. Abbinare con CODSITO_ALBERO è sbagliato: 29 chiavi esistono ma a circa 6 km e con 0 specie uguali.
- dbh_cm coincide con CIRCONF_CM diviso pi greco (rapporto 1,000, scarto 0,0 su 49 alberi con distanza fino a 3 m): non è una misura indipendente del censimento.

## 5. Altezza chioma da CHM contro Life Escapos

- CHM = DSM 2023 meno DTM 2023 (0,5 m). Per ogni albero Escapos: massimo del CHM entro un raggio pari alla semi-chioma misurata (minimo 1,5 m). Nessuno dei 50 è a meno di 3 m da un edificio UV.
- Scarto CHM massimo meno h_m: mediana +0,15 m, p10 +0,04, p90 +0,68, MAE 0,28 m, n 50. Con il 95° percentile: mediana -0,19 m, MAE 0,31 m. Correlazione 0,992; rapporto mediano 1,024.
- Per classe di h_m: sotto 6 m (7 alberi) +0,11 m; da 6 a 10 m (37) +0,15 m; da 10 m in su (6) +0,54 m, MAE 0,68 m.
- Cautela importante: un accordo così stretto (r 0,992, scarto quasi sempre positivo) non dimostra il CHM contro una misura indipendente. h_m ha precisione piena (per esempio 16,996858...) e dbh coincide con la circonferenza del censimento. La provenienza di h_m non è documentata e può derivare dallo stesso LiDAR. Non è una validazione. Serve una misura di campo, anche su pochi alberi, per dichiarare lo scarto vero.
- Sul censimento, 3.468 alberi in FA e FB, di cui 3.319 a più di 3 m da un edificio: massimo CHM entro 2 m, p10-p50-p90 = 1,8 - 6,7 - 14,4 m. 357 hanno CHM sotto 2 m (albero tolto o posizione sfalsata). La correlazione tra circonferenza e CHM è 0,042: va letta come limite del metodo, non come risultato, perché con 2 m di raggio nei filari si prendono anche i vicini. L'altezza per albero dal censimento richiede segmentazione delle chiome.

## 6. Giudizio sui riquadri per le ombre

| | FA | FB |
|---|---|---|
| Alberi | 1.614 (9,4 per ettaro) | 2.469 (14,4 per ettaro) |
| UV Regione | 972 | 1.459 |
| Edifici OSM con piani o altezza | 5 | 27 |
| Copertura cassone sull'area UV | 31,5% | 60,0% |
| Sito rilevato entro 3 m dall'albero | 44,2% | 51,6% |
| Alberi Life Escapos | 50 | 14 (tutti nell'area in comune) |
| nDSM meno uv_av, mediana | +0,07 m | +0,63 m |
| UV "in costruzione" nel 2011 | 36 | 1 |

- FB ha più alberi e più edifici, quindi più ombra da calcolare, e un abbinamento migliore con i siti rilevati.
- FA contiene tutti i 50 Escapos e ha l'UV 2011 più datata (36 in costruzione), con un'altezza nDSM più vicina a uv_av.
- La geometria da LiDAR è equivalente: 0% di nodata nell'nDSM di entrambi.
- Scelta rimessa all'utente. In sintesi: FB per più oggetti che fanno ombra, FA per avere un riferimento di chioma già abbinato (con la cautela del punto 5) e per essere il candidato D12.

## 7. Limiti

- Il censimento non ha altezza, chioma né data: l'altezza degli alberi viene dal CHM, con le incertezze del punto 5. Il DSM 2023 è di giugno (foglie), l'ombra invernale va trattata a parte.
- Escapos: solo 50 alberi, in gran parte Celtis australis, e provenienza di h_m non documentata. can_h_m non definito. CC BY-NC 4.0: nessuna redistribuzione.
- Siti alberi: datati 2014, solo una parte degli alberi, senza specie né chiave comune.
- Chiome senza forma: altezza e larghezza non descrivono la trasparenza (LAI presente solo per i 50 Escapos).

## File e riproduzione

Script in `script/`, campioni in `campioni/`, checksum in `manifest.json`.

Riprodurre dalla radice del progetto, dopo quello degli edifici (usa DSM, DTM e UV scaricati da lì): `docs/audit-firenze/verde/riproduci.sh` (circa 20 secondi).
