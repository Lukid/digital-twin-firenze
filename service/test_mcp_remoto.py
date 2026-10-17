#!/usr/bin/env python3
"""Test del server MCP via HTTP (F1, compito 1). Uso: service/.venv/bin/python service/test_mcp_remoto.py (richiede data/ locale).
Avvia il server HTTP in locale con un token di prova, elenca gli strumenti, esegue list_destinations e compute_walk_access sul Polo e confronta
con lo stesso calcolo via stdio; verifica il rifiuto di create_local_scenario, del token sbagliato e i limiti di chiamate e di calcoli lunghi.
Ogni server ha la sua cache temporanea: il confronto è fra due calcoli, non fra due letture della stessa cache."""
import asyncio, json, os, pathlib, shutil, socket, subprocess, sys, threading, time
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

HERE = pathlib.Path(__file__).parent
TMP = HERE / ".cache_test_remoto"; shutil.rmtree(TMP, ignore_errors=True)
PY, SERVER = sys.executable, str(HERE / "mcp_server.py")
TOKEN = "prova-locale-non-segreta"
POLO = "dst_university_w83537185"
WALK = {"baseline_id": "bas_firenze_novoli_20261009", "origins": {"kind": "address_points", "aoi_id": "aoi_firenze_novoli"}, "destination_ids": [POLO],
        "profile": {"speed_m_s": 1.2}, "thresholds_min": [5, 10, 15]}
SCN = {"baseline_id": "bas_firenze_novoli_20261009", "aoi_id": "aoi_firenze_novoli", "title": "prova", "interventions": []}
senza_cache = lambda r: {k: v for k, v in r.items() if k != "cached"}


def porta_libera():
    with socket.socket() as s: s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


async def chiamate(s):
    """Stesse chiamate sui due trasporti: strumenti, destinazioni del Polo, accessibilità al Polo."""
    await s.initialize()
    nomi = [x.name for x in (await s.list_tools()).tools]
    out = {"tools": nomi}
    for nome, args in (("list_destinations", {"aoi_id": "aoi_firenze_novoli", "category": "university", "name_query": "polo"}), ("compute_walk_access", WALK)):
        r = await s.call_tool(nome, args); assert not r.isError, (nome, r.content[0].text[:300])
        out[nome] = json.loads(r.content[0].text)
    return out


async def via_stdio():
    env = {**os.environ, "DT_CACHE_DIR": str(TMP / "stdio")}
    async with stdio_client(StdioServerParameters(command=PY, args=[SERVER], env=env)) as (r, w), ClientSession(r, w) as s:
        return await chiamate(s)


async def via_http(url):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {TOKEN}"}, timeout=300) as hc, \
            streamable_http_client(url, http_client=hc) as (r, w, _), ClientSession(r, w) as s:
        out = await chiamate(s)
        r = await s.call_tool("create_local_scenario", SCN)
        out["create"] = (r.isError, json.loads(r.content[0].text))
        return out


def main():
    t0 = time.time(); porta = porta_libera(); url = f"http://127.0.0.1:{porta}/mcp"
    env = {**os.environ, "DT_CACHE_DIR": str(TMP / "http"), "DT_SCENARIOS_DIR": str(TMP / "scenari"), "DT_MCP_TOKEN": TOKEN, "DT_MCP_RICHIESTE_MINUTO": "100"}
    srv = subprocess.Popen([PY, SERVER, "--http", "--port", str(porta)], env=env, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(100):   # attesa dell'avvio
            try: socket.create_connection(("127.0.0.1", porta), timeout=0.2).close(); break
            except OSError: time.sleep(0.2)
        else: raise RuntimeError("server HTTP non avviato: " + (srv.stderr.read() if srv.poll() is not None else ""))

        # 1. senza token o con token sbagliato: 401, prima di qualunque strumento
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}
        h = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
        assert httpx.post(url, json=init, headers=h).status_code == 401
        assert httpx.post(url, json=init, headers={**h, "Authorization": "Bearer sbagliato"}).status_code == 401

        # 2. stessi strumenti e stessi risultati via HTTP e via stdio
        rh, rs = asyncio.run(via_http(url)), asyncio.run(via_stdio())
        assert rh["tools"] == rs["tools"] and "create_local_scenario" in rh["tools"], (rh["tools"], rs["tools"])
        assert rh["list_destinations"] == rs["list_destinations"]
        assert [d["destination_id"] for d in rh["list_destinations"]["destinations"]] == [POLO], rh["list_destinations"]
        wh, ws = rh["compute_walk_access"], rs["compute_walk_access"]
        assert not wh["cached"] and not ws["cached"], "le due cache temporanee dovevano essere vuote"
        assert senza_cache(wh) == senza_cache(ws), "compute_walk_access diverso fra HTTP e stdio"
        m = {x["metric_id"]: x["value"] for x in wh["headline_metrics"]}
        print("Polo via HTTP:", wh["job_id"], {k: v for k, v in m.items() if k.startswith("served_share")})

        # 3. create_local_scenario rifiutato da remoto, senza scrivere scenari
        err, r = rh["create"]
        assert err and r["error"]["code"] == "outside_capability" and "sola lettura" in r["error"]["message"], r
        assert not (TMP / "scenari").exists() or not list((TMP / "scenari").iterdir())
    finally:
        srv.terminate(); srv.wait(10)

    # 4. limiti del servizio remoto, sulla classe che li applica (senza server: niente attese)
    sys.path.insert(0, str(HERE)); os.environ["DT_CACHE_DIR"] = str(TMP / "unit")
    import core, mcp_server as M
    R = M.Remoto(richieste_minuto=3, job_lunghi=1)
    r = [R.esegui("list_scenarios", {}, "1.2.3.4") for _ in range(4)]
    assert all("error" not in x for x in r[:3]) and r[3]["error"]["code"] == "limit_exceeded", r[3]
    assert "error" not in R.esegui("list_scenarios", {}, "5.6.7.8")   # il limite è per client
    R = M.Remoto(richieste_minuto=100, job_lunghi=1); dentro, esce = threading.Event(), threading.Event()
    vero = core.run_tool
    def lento(n, a): dentro.set(); esce.wait(10); return {"ok": n}
    core.run_tool = lento
    try:
        th = threading.Thread(target=R.esegui, args=("compute_shadow", {}, "a")); th.start(); dentro.wait(5)
        r = R.esegui("compare_scenarios", {}, "b")
        assert r["error"]["code"] == "limit_exceeded", r
        assert R.esegui("list_scenarios", {}, "b") == {"ok": "list_scenarios"}   # gli strumenti brevi passano anche durante un calcolo lungo
        esce.set(); th.join()
        assert R.esegui("compare_scenarios", {}, "b") == {"ok": "compare_scenarios"}   # posto liberato
    finally:
        core.run_tool = vero
    assert core.validate("create_local_scenario", "output", R.esegui("create_local_scenario", SCN, "a")) == []   # l'errore rispetta il contratto

    shutil.rmtree(TMP, ignore_errors=True)
    print(f"OK test MCP remoto in {time.time() - t0:.1f} s")


if __name__ == "__main__": main()
