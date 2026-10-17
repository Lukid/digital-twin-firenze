# Installare il server MCP remoto

Istruzioni per mettere `dt-firenze` su una macchina raggiungibile dai colleghi, in sola lettura. I file sono pronti ma non installati: dove e quando installare lo decide Luca (D28: macchina di prova).

## Cosa fa il server remoto

- Protocollo MCP su HTTP (streamable HTTP), percorso `/mcp` (anche `/mcp/`). Stesso nucleo (`service/core.py`) e stessi risultati del server stdio usato in locale.
- Sola lettura: `create_local_scenario` risponde sempre `outside_capability`. Gli scenari salvati restano interrogabili (`list_scenarios`, `compute_shadow` con `scenario_id`, `compare_scenarios`).
- Limiti: chiamate di strumento al minuto per indirizzo del client e calcoli lunghi (`compute_shadow`, `compare_scenarios`) contemporanei. Oltre il limite la risposta è `limit_exceeded`, senza attesa.
- Token facoltativo: con `DT_MCP_TOKEN` impostata ogni richiesta deve avere `Authorization: Bearer <token>`, altrimenti risponde 401.
- Nessun segreto nel repository. I valori stanno nel file d'ambiente della macchina.

## Variabili d'ambiente

Nomi in `service/.env.example`. Valori consigliati:

| Variabile | Default | Consiglio |
|---|---|---|
| `DT_MCP_TRANSPORT` | stdio | `http` (oppure argomento `--http`) |
| `DT_MCP_HOST` | 127.0.0.1 | 127.0.0.1 dietro un proxy inverso con HTTPS; mai 0.0.0.0 senza proxy e token |
| `DT_MCP_PORT` | 8793 | porta libera sulla macchina, non esposta direttamente |
| `DT_MCP_RICHIESTE_MINUTO` | 30 | 30: un assistente fa 5-15 chiamate per domanda |
| `DT_MCP_JOB_LUNGHI` | 1 | 1: un `compute_shadow` usa un processore per decine di secondi o minuti |
| `DT_MCP_TOKEN` | nessuno | un valore casuale lungo (per esempio `openssl rand -hex 32`), consegnato ai colleghi a parte |
| `DT_MCP_HOST_AMMESSI` | nessuno | il nome pubblico del servizio e `127.0.0.1:8793`, separati da virgola: attiva il controllo dell'intestazione Host |
| `DT_CACHE_DIR` | `service/cache/firenze_novoli` | lasciare il default (deve stare dentro il clone) |
| `DT_AOI` | `aoi_firenze_novoli` | lasciare il default |

Il limite per client usa l'indirizzo che vede il server: dietro un proxy inverso è quello del proxy, quindi il limite diventa complessivo. Se serve un limite per persona, va messo nel proxy.

## Passi

Come utente amministratore della macchina (gli unici passi che richiedono privilegi):

```
useradd --system --home-dir /opt/dt-firenze --shell /usr/sbin/nologin dtfirenze
git clone <url del repository> /opt/dt-firenze
chown -R dtfirenze:dtfirenze /opt/dt-firenze
mkdir -p /etc/dt-firenze && touch /etc/dt-firenze/mcp.env
chown root:dtfirenze /etc/dt-firenze/mcp.env && chmod 640 /etc/dt-firenze/mcp.env
```

Scrivere in `/etc/dt-firenze/mcp.env` le variabili della tabella (almeno `DT_MCP_TRANSPORT=http` e `DT_MCP_TOKEN`).

Come utente `dtfirenze` (`sudo -u dtfirenze -s /bin/bash`), dentro `/opt/dt-firenze`:

```
python3.12 -m venv pipeline/.venv && pipeline/.venv/bin/pip install -r pipeline/requirements.txt
python3.12 -m venv service/.venv  && service/.venv/bin/pip install -r service/requirements.txt
# ricreare data/: sezione "Dati" più sotto
make test-fast       # deve passare prima di avviare il servizio
```

Se `python3.12 -m venv` fallisce per mancanza di `ensurepip`, installare il pacchetto `python3.12-venv` della distribuzione.

Di nuovo come amministratore:

```
cp /opt/dt-firenze/service/remoto/dt-firenze-mcp.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now dt-firenze-mcp
systemctl status dt-firenze-mcp
```

L'unità avvia il server come `dtfirenze`, senza privilegi, con il file system in sola lettura tranne la cache del servizio e la cache delle ombre degli scenari.

## Proxy inverso e HTTPS

Il server non gestisce HTTPS. Davanti va il proxy inverso già usato sulla macchina, con un certificato valido, che inoltra `https://<nome>/mcp/` a `http://127.0.0.1:8793/mcp/`. Accorgimenti:

- tempo massimo di risposta di almeno 10 minuti: `compare_scenarios` senza cache dura alcuni minuti;
- niente buffering della risposta, se il proxy lo permette;
- limite sulla dimensione delle richieste: 1 MB basta.

## Dati

Il servizio legge `data/` (ignorata da git, circa 1,7 GB) e i risultati versionati nel repository.

Modo consigliato: copiare `data/` già costruita dalla macchina di Luca (per esempio con `rsync -a data/ <macchina>:/opt/dt-firenze/data/`). È l'unico modo per avere gli stessi job_id dei manifest versionati.

Ricostruire da zero oggi non funziona fino in fondo: l'estratto OSM della baseline (2026-10-08) non è più scaricabile e il Comune ha rinumerato i civici, per cui `network/percorsi_firenze.py` e alcuni test non trovano più i civici dei percorsi campione. Il servizio funziona lo stesso, con le stesse metriche ma job_id diversi (dettagli in `docs/REPORT-AGENTE-F1.md`, compito 0). Ordine dei passi (circa un'ora, scarica dalla rete):

```
DT_DAY=20261009 OSM_URL=<estratto OSM con la data nel nome> pipeline/.venv/bin/python pipeline/fonti_firenze.py acquire alberi civici barriere rifugi_aree rifugi_bibl uv dtm dsm osm gtfs_tram gtfs_bus tram_fermate scuole cm_edscol
DT_DAY=20261010 pipeline/.venv/bin/python pipeline/fonti_firenze.py acquire aree_pedonali catasto landsat_st sir_termo arpat
DT_DAY=20261016 pipeline/.venv/bin/python pipeline/fonti_firenze.py acquire gtfs_tram gtfs_bus
git checkout -- pipeline/snapshots        # gli snapshot versionati restano quelli della baseline
pipeline/.venv/bin/python pipeline/norm_firenze.py
network/build_firenze.sh
geometry/build_firenze.sh
bash shadow/run.sh
bash analysis/run.sh
bash scenarios/run.sh
git checkout -- network geometry shadow analysis scenarios   # i risultati versionati non si riscrivono dal server
```

`DT_DAY` va fissato ai giorni degli snapshot registrati in `pipeline/snapshots/`: così i file finiscono nelle cartelle che la pipeline si aspetta. Alcune fonti cambiano a ogni scarico (WFS, pagine HTML, finestra mobile del GTFS dei bus, censimento degli alberi aggiornato ogni giorno).

## Aggiornare

```
sudo -u dtfirenze git -C /opt/dt-firenze pull
sudo -u dtfirenze make -C /opt/dt-firenze test-fast
systemctl restart dt-firenze-mcp
```

La cache del servizio si svuota da sola quando cambiano il codice dei motori o i file di dati che leggono. Se si aggiornano i dati, riavviare il servizio.

## Cache

- `service/cache/firenze_novoli/`: job, manifest e confronti già calcolati. Chiave = hash della richiesta. Cresce di pochi MB per job d'ombra; si può cancellare a servizio fermo.
- `data/norm/firenze_novoli/scenarios/jobs/`: ombre degli scenari. Se è vuota, il primo `compare_scenarios` dura alcuni minuti.
- Dopo l'installazione conviene scaldare la cache con le domande di `nl/firenze_novoli/` (vedere `nl/firenze_novoli/REPORT-REMOTO.md`).

## Come si collega un collega

Da un assistente che supporta MCP su HTTP, aggiungere un server con URL `https://<nome>/mcp/` e intestazione `Authorization: Bearer <token>`. Poi incollare il testo di `service/PROMPT-AGENTE.md` come istruzioni. Per Claude Code, in `.mcp.json` del progetto del collega:

```
{"mcpServers": {"dt-firenze": {"type": "http", "url": "https://<nome>/mcp/", "headers": {"Authorization": "Bearer ${DT_MCP_TOKEN}"}}}}
```

## Verifica dopo l'installazione

Sulla macchina, con il servizio attivo:

```
service/.venv/bin/python service/test_mcp_remoto.py
```

Il test avvia un secondo server su una porta libera e non tocca quello in servizio.
