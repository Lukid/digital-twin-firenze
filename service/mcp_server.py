#!/usr/bin/env python3
"""Server MCP stdio. Ogni strumento passa da core.run_tool: input validati contro lo schema, nessun SQL o codice libero.
Gli errori di strumento sono restituiti come risultato con isError=true e codice (ambiguous_destination, outside_capability, ...)."""
import asyncio, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import core
import mcp.types as t
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

DESC = {
    "list_approved_sources": "Fonti dati approvate per tema e area, con snapshot, licenza, uso consentito, periodo del contenuto e lacune.",
    "inspect_dataset": "Schema, unità, estensione, periodo, qualità e licenza di una fonte o di uno snapshot.",
    "list_destinations": "Destinazioni (Polo universitario, scuole, fermate del tram) con ID, ingressi e stato di verifica. name_query accetta alias italiani (polo, università, vamba, tram, fermata regione, torre degli agli). Usarlo per ottenere il destination_id: non scegliere mai per nome.",
    "compute_walk_access": "Accessibilità pedonale dai civici (punti d'indirizzo) di Firenze Novoli verso UNA destinazione (destination_id esatto, con origins address_points e aoi_id). Restituisce job_id, dataset, parametri, metriche e limiti; il risultato è in cache se già calcolato.",
    "get_job_status": "Stato e parametri di un job già eseguito.", "get_result_manifest": "Manifest completo (metodo, dataset, metriche, limiti, asset) di un job.",
    "compute_shadow": "Ombra geometrica su percorsi (route_id campione R01...R10, o geometrie) per data e orari locali Europe/Rome: frazione in ombra e minuti al sole camminando, con intervalli di sensibilità. Con obstacles=buildings_trees_and_lidar_vegetation aggiunge alberi censiti e vegetazione LiDAR. Con scenario_id (obstacles=buildings_and_scenario) somma gli interventi dello scenario agli edifici documentati. Orari con sole sotto 5 gradi hanno stato esplicito e nessun numero. Job lungo: tenere basso il numero di orari.",
    "create_local_scenario": "Crea uno scenario locale versionato (nuovi alberi con dimensione di classe scenario, pensiline con quota d'imposta e tetto) a partire dalla baseline congelata. Segnala interventi dentro edifici o su carreggiata senza marciapiede; la fattibilità resta sempre ignota. Rimozioni e modifiche non sono supportate.",
    "compare_scenarios": "Confronto su condizioni comuni. Con baseline_id e scenario_ids: delta di ombra e minuti al sole su R01 e percorsi campione, area di attesa, tratti più usati pesati per civici (non persone), effetto sull'accessibilità; indicatori separati, ordinamento solo se si danno i pesi. Con manifest_ids e metric_ids: delta fra manifest di compute_shadow. Il calcolo del confronto fra scenari può richiedere alcuni minuti se le ombre non sono in cache."}
server = Server("dt-firenze", instructions="Calcoli deterministici sul pilota di Firenze, Novoli - Firenze Nova (aoi_firenze_novoli). Non dire di aver calcolato nulla se non c'è un job riuscito; riporta job_id, dataset, parametri e limiti. Se una destinazione è ambigua, chiedi all'utente.")


@server.list_tools()
async def _list():
    return [t.Tool(name=n, description=DESC[n], inputSchema=core.schema_for_client(n)) for n in core.TOOLS]


@server.call_tool(validate_input=False)   # la validazione vera è nel nucleo, con lo schema dei contratti
async def _call(name, arguments):
    r = await asyncio.to_thread(core.run_tool, name, arguments or {})
    return t.CallToolResult(content=[t.TextContent(type="text", text=json.dumps(r, ensure_ascii=False))], structuredContent=r, isError="error" in r)


async def main():
    async with stdio_server() as (r, w): await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__": asyncio.run(main())
