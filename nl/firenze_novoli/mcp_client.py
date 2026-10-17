#!/usr/bin/env python3
"""Client MCP minimo per la verifica NL: parla con il vero server dt-firenze via stdio, oppure via HTTP se DT_MCP_URL è impostata
(con DT_MCP_TOKEN, se il server la chiede).
Uso: service/.venv/bin/python nl/firenze_novoli/mcp_client.py tools
     service/.venv/bin/python nl/firenze_novoli/mcp_client.py call <tool> '<json argomenti>'"""
import asyncio, contextlib, json, os, pathlib, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVER = StdioServerParameters(command=str(ROOT / "service/.venv/bin/python"), args=[str(ROOT / "service/mcp_server.py")])


@contextlib.asynccontextmanager
async def trasporto():
    url = os.environ.get("DT_MCP_URL")
    if not url:
        async with stdio_client(SERVER) as (r, w): yield r, w
        return
    import httpx
    from mcp.client.streamable_http import streamable_http_client
    tok = os.environ.get("DT_MCP_TOKEN")
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {tok}"} if tok else {}, timeout=600) as hc, streamable_http_client(url, http_client=hc) as (r, w, _):
        yield r, w


async def main(argv):
    async with trasporto() as (r, w), ClientSession(r, w) as s:
        init = await s.initialize()
        if argv[0] == "tools":
            tools = (await s.list_tools()).tools
            print(json.dumps({"instructions": init.instructions, "tools": [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in tools]}, ensure_ascii=False, indent=1))
            return 0
        res = await s.call_tool(argv[1], json.loads(argv[2]) if len(argv) > 2 else {})
        print(json.dumps({"isError": res.isError, "result": json.loads(res.content[0].text)}, ensure_ascii=False, indent=1))
        return 0


if __name__ == "__main__":
    if not sys.argv[1:] or sys.argv[1] not in ("tools", "call"): print(__doc__); sys.exit(2)
    sys.exit(asyncio.run(main(sys.argv[1:])))
