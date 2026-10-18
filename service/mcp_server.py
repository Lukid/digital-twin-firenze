#!/usr/bin/env python3
"""Server MCP. Ogni strumento passa da core.run_tool: input validati contro lo schema, nessun SQL o codice libero.
Gli errori di strumento sono restituiti come risultato con isError=true e codice (ambiguous_destination, outside_capability, ...).

Trasporti: stdio (default, quello di .mcp.json) oppure HTTP (streamable HTTP del protocollo MCP, percorso /mcp o /mcp/) per l'uso remoto.
    mcp_server.py                              stdio
    mcp_server.py --http [--host H --port P]   HTTP; anche con DT_MCP_TRANSPORT=http
In HTTP il server è in sola lettura (create_local_scenario risponde outside_capability) e ha due limiti, da variabili d'ambiente:
    DT_MCP_HOST, DT_MCP_PORT        indirizzo d'ascolto (default 127.0.0.1:8793)
    DT_MCP_RICHIESTE_MINUTO         chiamate di strumento al minuto per indirizzo del client (default 30)
    DT_MCP_JOB_LUNGHI               calcoli lunghi contemporanei, compute_shadow e compare_scenarios (default 1)
    DT_MCP_TOKEN                    se impostata, ogni richiesta deve portare Authorization: Bearer <valore>
    DT_MCP_HOST_AMMESSI             nomi host ammessi nell'intestazione Host, separati da virgola (protezione dal DNS rebinding)"""
import argparse, asyncio, collections, hmac, json, os, pathlib, sys, threading, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import core
import mcp.types as t
from mcp.server.lowlevel import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server

DESC = {
    "list_approved_sources": "Fonti dati approvate per tema e area, con snapshot, licenza, uso consentito, periodo del contenuto e lacune.",
    "inspect_dataset": "Schema, unità, estensione, periodo, qualità e licenza di una fonte o di uno snapshot.",
    "list_destinations": "Destinazioni (Polo universitario, scuole, fermate del tram) con ID, ingressi e stato di verifica. name_query accetta alias italiani (polo, università, vamba, tram, san donato, fermata regione, torre degli agli). Il Polo ha un ingresso per edificio (D1, D4, D5, D6, D10, D14, D15): senza entrance_ids vince il più vicino. Usarlo per ottenere il destination_id: non scegliere mai per nome.",
    "list_scenarios": "Scenari salvati (id scn_fi_*), con titolo, versione, baseline e riepilogo degli interventi. Usarlo per ottenere gli scenario_ids di compute_shadow e compare_scenarios.",
    "compute_walk_access": "Accessibilità pedonale dai civici (punti d'indirizzo) di Firenze Novoli verso una destinazione, o verso almeno una di più destinazioni (destination_ids esatti, con origins address_points e aoi_id): con più destinazioni per ogni civico conta la più vicina. Metriche: civici raggiunti per soglia (served_count_*) e quote sul totale (served_share_*). Restituisce job_id, dataset, parametri, metriche e limiti; il risultato è in cache se già calcolato.",
    "get_job_status": "Stato e parametri di un job già eseguito.", "get_result_manifest": "Manifest completo (metodo, dataset, metriche, limiti, asset) di un job.",
    "compute_shadow": "Ombra geometrica su percorsi (route_id campione R01...R10, o geometrie) per data e orari locali Europe/Rome: frazione in ombra e minuti al sole camminando, con intervalli di sensibilità. Con obstacles=buildings_trees_and_lidar_vegetation aggiunge alberi censiti e vegetazione LiDAR. Con scenario_id (obstacles=buildings_and_scenario) somma gli interventi dello scenario agli edifici documentati. Orari con sole sotto 5 gradi hanno stato esplicito e nessun numero. Job lungo: tenere basso il numero di orari.",
    "create_local_scenario": "Crea uno scenario locale versionato (nuovi alberi con dimensione di classe scenario, pensiline con quota d'imposta e tetto) a partire dalla baseline congelata. Segnala interventi dentro edifici o su carreggiata senza marciapiede; la fattibilità resta sempre ignota. Rimozioni e modifiche non sono supportate.",
    "compare_scenarios": "Confronto su condizioni comuni. Con baseline_id e scenario_ids: delta di ombra e minuti al sole su R01 e percorsi campione, area di attesa, tratti più usati pesati per civici (non persone), effetto sull'accessibilità; indicatori separati, nessun ordinamento né punteggio unico (con weights risponde outside_capability). Con manifest_ids e metric_ids: delta fra manifest di compute_shadow. Il calcolo del confronto fra scenari può richiedere alcuni minuti se le ombre non sono in cache.",
    "get_source_card": "Schede delle fonti: senza source_id l'indice (una riga per fonte, con licenza, uso consentito e data del dato), con source_id la scheda completa (editore, catalogo, licenza ed evidenza, date degli scarichi, campi usati, controlli, limiti). Usarla per citare fonti e licenze nelle risposte. Le stesse schede sono anche risorse MCP (schede://).",
    "estimate_residents": "Residenti stimati raggiunti entro le soglie di un job di compute_walk_access già eseguito, accanto alla quota dei civici. Stima: residenti del censimento 2011 per sezione ripartiti in parti uguali sui civici della sezione, civici senza abitazioni contati come gli altri; con intervallo di velocità, sensibilità sui soli civici neri, fonti e limiti.",
    "get_route_exposure": "Percorsi campione (R01-R10, RC1-RC5) più esposti al sole in una data già calcolata (date, per esempio 2026-07-15): per ogni orario metri al sole, minuti al sole camminando, tratto al sole più lungo, classifica per metri e per minuti, job_id di compute_shadow per percorso. Date non calcolate: errore con le date disponibili.",
    "get_shaded_access": "Civici e residenti stimati che arrivano al rifugio climatico più vicino camminando soprattutto all'ombra (almeno il 50% del percorso in ombra, sensibilità 40% e 60%; soglia scelta da noi, da validare con l'ufficio), accanto a quelli che arrivano e basta, entro 10 e 15 minuti. Già calcolato per il job dei 7 rifugi (job_e1e75455f7511f7d) alle 14:00 del 15 luglio 2026 (date 2026-07-15), sull'asse del percorso più breve; intervallo dalla vegetazione, caso solo edifici, fonti e limiti. Combinazioni non calcolate: errore con quelle disponibili."}
ISTRUZIONI = "Calcoli deterministici sul pilota di Firenze, Novoli - Firenze Nova (aoi_firenze_novoli). Non dire di aver calcolato nulla se non c'è un job riuscito; riporta job_id, dataset, parametri e limiti. Se una destinazione è ambigua, chiedi all'utente."
SOLA_LETTURA = {"create_local_scenario"}   # strumenti che scrivono dati di progetto: spenti nel servizio remoto
JOB_LUNGHI = {"compute_shadow", "compare_scenarios"}


class Remoto:
    """Regole del servizio remoto: sola lettura, limite di chiamate per client, limite di calcoli lunghi contemporanei."""
    def __init__(s, richieste_minuto, job_lunghi):
        s.rpm, s.finestre, s.lock = richieste_minuto, collections.defaultdict(collections.deque), threading.Lock()
        s.lunghi = threading.BoundedSemaphore(job_lunghi)

    def ammesso(s, client):
        """Finestra scorrevole di 60 s per indirizzo del client."""
        with s.lock:
            q, ora = s.finestre[client], time.monotonic()
            while q and ora - q[0] > 60: q.popleft()
            if len(q) >= s.rpm: return False
            q.append(ora); return True

    def esegui(s, name, args, client):
        if name in SOLA_LETTURA:
            return core.err("outside_capability", f"{name} non è disponibile sul servizio remoto, che è in sola lettura. Usare gli scenari salvati (list_scenarios).")
        if not s.ammesso(client):
            return core.err("limit_exceeded", f"Più di {s.rpm} chiamate al minuto da questo client: riprovare fra un minuto.")
        if name not in JOB_LUNGHI: return core.run_tool(name, args)
        if not s.lunghi.acquire(blocking=False):
            return core.err("limit_exceeded", "Il servizio sta già eseguendo il numero massimo di calcoli lunghi: riprovare fra qualche minuto.")
        try: return core.run_tool(name, args)
        finally: s.lunghi.release()


def crea_server(remoto=None):
    server = Server("dt-firenze", instructions=ISTRUZIONI)

    @server.list_tools()
    async def _list():
        desc = dict(DESC)
        if remoto:
            for n in SOLA_LETTURA: desc[n] = "Non disponibile su questo servizio remoto (sola lettura): risponde sempre outside_capability. " + desc[n]
        return [t.Tool(name=n, description=desc[n], inputSchema=core.schema_for_client(n)) for n in core.TOOLS]

    @server.list_resources()
    async def _risorse():
        return [t.Resource(uri=f"schede://{p.name}", name=p.stem, mimeType="text/markdown",
                           description="Indice delle schede delle fonti" if p.stem == "INDEX" else f"Scheda della fonte {p.stem}") for p in sorted(core.SCHEDE.glob("*.md"))]

    @server.read_resource()
    async def _leggi(uri):
        nome = str(uri).removeprefix("schede://")
        p = core.SCHEDE / nome
        if "/" in nome or not nome.endswith(".md") or not p.is_file(): raise ValueError(f"Risorsa sconosciuta: {uri}")
        return [ReadResourceContents(content=p.read_text(), mime_type="text/markdown")]

    @server.call_tool(validate_input=False)   # la validazione vera è nel nucleo, con lo schema dei contratti
    async def _call(name, arguments):
        if remoto:
            req = server.request_context.request
            client = req.client.host if req is not None and req.client else "?"
            r = await asyncio.to_thread(remoto.esegui, name, arguments or {}, client)
        else:
            r = await asyncio.to_thread(core.run_tool, name, arguments or {})
        return t.CallToolResult(content=[t.TextContent(type="text", text=json.dumps(r, ensure_ascii=False))], structuredContent=r, isError="error" in r)

    return server


async def main_stdio():
    server = crea_server()
    async with stdio_server() as (r, w): await server.run(r, w, server.create_initialization_options())


def app_http(token=None, richieste_minuto=30, job_lunghi=1, host_ammessi=None):
    """Applicazione ASGI con il solo percorso /mcp. Il token, se c'è, si confronta a tempo costante."""
    import contextlib
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from mcp.server.transport_security import TransportSecuritySettings

    sicurezza = TransportSecuritySettings(enable_dns_rebinding_protection=bool(host_ammessi), allowed_hosts=host_ammessi or [], allowed_origins=[])
    sm = StreamableHTTPSessionManager(app=crea_server(Remoto(richieste_minuto, job_lunghi)), stateless=True, json_response=True, security_settings=sicurezza)

    class McpAsgi:   # oggetto ASGI e non funzione: Route lo passa così com'è, senza trasformarlo in richiesta e risposta
        async def __call__(self, scope, receive, send):
            if token:
                h = dict(scope.get("headers") or []).get(b"authorization", b"").decode("latin-1")
                if not hmac.compare_digest(h.encode(), f"Bearer {token}".encode()):
                    return await JSONResponse({"error": "token mancante o non valido"}, status_code=401)(scope, receive, send)
            await sm.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def ciclo(app):
        async with sm.run(): yield

    app = McpAsgi()   # /mcp e /mcp/: un redirect fra i due non è seguito da tutti i client
    return Starlette(routes=[Route("/mcp", endpoint=app, methods=["GET", "POST", "DELETE"]), Route("/mcp/", endpoint=app, methods=["GET", "POST", "DELETE"])], lifespan=ciclo)


def main_http(host, port):
    import uvicorn
    amm = [h.strip() for h in os.environ.get("DT_MCP_HOST_AMMESSI", "").split(",") if h.strip()]
    app = app_http(os.environ.get("DT_MCP_TOKEN") or None, int(os.environ.get("DT_MCP_RICHIESTE_MINUTO", "30")), int(os.environ.get("DT_MCP_JOB_LUNGHI", "1")), amm)
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Server MCP dt-firenze: stdio (default) o HTTP in sola lettura.")
    p.add_argument("--http", action="store_true", default=os.environ.get("DT_MCP_TRANSPORT") == "http")
    p.add_argument("--host", default=os.environ.get("DT_MCP_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("DT_MCP_PORT", "8793")))
    a = p.parse_args()
    main_http(a.host, a.port) if a.http else asyncio.run(main_stdio())
