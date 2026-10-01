# T09: ombre Z2 (analisi B)

Data: 1 ottobre 2026. Redatto dall'agente T09 e salvato dall'integratore. Test `pipeline/.venv/bin/python shadow/test_ombre.py`: tutti OK (rieseguito dall'integratore). Analisi completa `shadow/run.sh`, circa 8 minuti. Job e manifest validi sugli schemi di `contracts/`. Risultati `not_validated_locally`.

## Metodo

- Sole: algoritmo NOAA/Meeus implementato nel progetto, azimut da Nord, elevazione geometrica. Europe/Rome convertito in UTC con il database dei fusi. Ore inesistenti (29/3 02:30) o ambigue (25/10 02:30) danno errore esplicito.
- Ombra di un volume = somma di Minkowski fra impronta e segmento [z_lo, z_hi]: esatta anche per impronte concave e con buchi. Un volume sospeso non ombreggia il suolo sotto di sé.
- Chioma = ellissoide opaco fra imposta e cima, tronco trascurato; il cilindro è l'alternativa come limite superiore.
- Unione di tutte le ombre in un solo poligono. Frazione = lunghezza(percorso ∩ unione) / lunghezza(percorso).
- Terreno quasi piano, dichiarato: ogni volume è riferito alla propria quota base.
- Sole sotto l'orizzonte: stato `sole_sotto_orizzonte`, nessun calcolo. Sotto 5°: `sole_basso_fuori_supporto` (il margine dei dati, 450 m, non copre le ombre lunghe degli edifici alti).

## Test

- Sole: 6 riferimenti di un algoritmo solare di precisione calcolati offline (scarto sotto 0,015°) e 3 massimi giornalieri analitici.
- Cambio d'ora: offset, 92 e 100 passi da 15 min, culminazione che salta di 1 h.
- Geometria: cubo analitico, volume sospeso, unione di volumi sovrapposti, corte con buco, chioma ellittica, sole sotto l'orizzonte.
- Dati reali: base ≤ alberi min ≤ tipico ≤ max; cilindro > ellissoide.
- Contratti: `job_id` deterministico, uguale all'hash dell'input.
- Convergenza (canyon sintetico): passo temporale 15/5/1 min → 0,771/0,777/0,779; passo spaziale 2/1/0,5 m → scarto 0,66/0,34/0,16 punti.

## Verifica raster indipendente (`verifica_raster.py`)

Ray casting su griglia a 0,5 m, finestra 250×250 m in Z2, 5 istanti × 5 casi: scarto medio della frazione d'ombra al suolo 0,5 punti, massimo 1,1. Il ray casting sul DSM 2021 è solo informativo (0,38 contro 0,50 con sole alto: bias del DSM, veicoli, terreno non piano), non è un riferimento.

## R01 Pellico → Battisti (755 m, 15 settembre, asse della rete)

Frazione in ombra; fra parentesi l'intervallo (altezze min/max di T05; chiome min/max).

- 7:45-8:30: edifici 0,913 (0,911-0,913); edifici + alberi tipico 0,913. Minuti al sole su 10,5: 0,95.
- 12:30-13:30: edifici 0,458 (0,450-0,461); con alberi 0,466 (0,458-0,542). Minuti al sole 5,72 → 5,64 (4,87-5,71).
- 16:00-16:30: edifici 0,662 (0,655-0,673); con alberi 0,682 (0,662-0,705). Minuti al sole 3,50 → 3,28 (3,04-3,50).
- 8-18: edifici 0,549 (0,540-0,560); con alberi 0,558 (0,550-0,586). Minuti al sole 4,72 → 4,63 (4,33-4,71).
- 21 giugno 12:30-13:30: 0,060 (0,055-0,067), con alberi fino a 0,105; mattina 0,933.
- 1 ottobre 12:30-13:30: 0,519 (0,504-0,534), con alberi 0,529 (0,521-0,611); pomeriggio 0,729. Alle 7:45 il sole è sotto 5°: orario escluso con stato esplicito.
- R03-R08 e le altre date: `shadow/out/riepilogo.json`.

## Sensibilità

- Altezze (±0,5 m measured, ±1,36 m derived, fino a 2,05 m vicino alla vegetazione): ±0,6-1,5 punti.
- Alberi: il caso tipico aggiunge +0,8 punti a mezzogiorno e +2 al pomeriggio, come l'incertezza delle altezze. Solo le chiome massime cambiano chiaramente (fino a +8 punti). Ellissoide al posto del cilindro: circa -1 punto.
- **Lato del marciapiede: incertezza dominante.** R01 spostata di 3 m a sinistra o a destra cambia fino a 20 punti: 21 giugno a mezzogiorno 0,060 → 0,113 / 0,266; 1 ottobre pomeriggio 0,729 → 0,705 / 0,793.
- Passi scelti 5 min e 1 m: sui minuti al sole lo scarto rispetto a 1 min è al massimo 0,01 min; campionamento 2/1/0,5 m → 0,20/0,11/0,06 punti.

## Limiti

- Percorsi sull'asse della rete: il lato del marciapiede non è noto.
- Il campo `sospeso` è ignoto nella fonte: portici e coperture OSM sono trattati come volumi pieni (limite superiore dell'ombra al suolo). **Incoerenza con la scena T08**, che disegna le coperture come volumi sospesi: da allineare.
- Alberi solo stimati per classe; 463 chiome con imposta limitata a metà altezza; esclusi 3 alberi dentro edifici e 4 volumi senza altezza. Inventario incompleto: non è l'ombra reale.
- Ombra binaria, nessuna conversione in gradi o comfort. Velocità costante 1,2 m/s, senza attese agli attraversamenti.
- Il `job_id` dipende dall'input, non dal codice: se cambia la logica va aumentata `VERSIONE` in `ombre.py`.

## Per T07

```
compute_shadow(baseline_id, receivers, when, method, scenario_id=None, scenario_volumes=None,
               walk_speed_m_s=1.2, *, casi=None, fasce=None, el_min=5.0, asset_times=(),
               asset_casi=("base",), asset_bbox=None, out_dir=None, scenario_version=1)
  -> {"job", "manifest", "righe", "sintesi", "assets"}
```

- `receivers`, `when`, `method` seguono `compute_shadow.input` di `mcp.schema.json`. L'enum `method.obstacles` va esteso con `buildings_and_trees`.
- `scenario_volumes` = [{id, geometry, z_lo, z_hi}] per volumi di scenario (es. pensiline).
- `OraInesistente` e `OraAmbigua` sono sottoclassi di `ValueError`: vanno mappate su `tool_error`.
- Costo: circa 2 minuti per 7 percorsi × 42 orari × 7 casi.

## File

`ombre.py`, `verifica_raster.py`, `run.py`, `run.sh`, `test_ombre.py`; output in `shadow/out/` (3 GeoJSON per il 15 settembre alle 8:00, 13:00 e 16:30, baseline e alberi tipico; `riepilogo.json`; `verifica_raster.json`) e `shadow/manifest/`. Tabelle complete in `data/norm/shadow/` (non versionata). pvlib installata in `pipeline/.venv` solo per le costanti di riferimento, non usata a runtime.
