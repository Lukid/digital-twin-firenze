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
    "list_destinations": "Destinazioni (scuole, fermate) con ID e ingressi e stato di verifica. Usarlo per ottenere il destination_id: non scegliere mai per nome.",
    "compute_walk_access": "Accessibilità pedonale dai civici SIT di Z2 verso UNA destinazione (destination_id esatto). Restituisce job_id, dataset, parametri, metriche e limiti; il risultato è in cache se già calcolato.",
    "get_job_status": "Stato e parametri di un job già eseguito.", "get_result_manifest": "Manifest completo (metodo, dataset, metriche, limiti, asset) di un job.",
    "compute_shadow": "Ombra geometrica su percorsi (route_id campione come R01, o geometrie) per data e orari locali Europe/Rome: frazione in ombra e minuti al sole camminando, con intervalli di sensibilità. Calcolo solo sulla baseline (niente scenari). Orari con sole sotto 5 gradi hanno stato esplicito e nessun numero. Job lungo: tenere basso il numero di orari.", "create_local_scenario": "NON ANCORA DISPONIBILE: restituisce outside_capability.",
    "compare_scenarios": "NON ANCORA DISPONIBILE: restituisce outside_capability."}
server = Server("dt-pisa", instructions="Calcoli deterministici sul pilota Z2 di Pisa. Non dire di aver calcolato nulla se non c'è un job riuscito; riporta job_id, dataset, parametri e limiti. Se una destinazione è ambigua, chiedi all'utente.")


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
