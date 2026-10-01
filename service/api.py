#!/usr/bin/env python3
"""API HTTP locale minima, solo 127.0.0.1. POST /tools/<nome> con corpo JSON; GET /tools elenca gli strumenti. Nessuna autenticazione: non esporre."""
import json, pathlib, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import core


class H(BaseHTTPRequestHandler):
    def _send(self, code, o):
        b = json.dumps(o, ensure_ascii=False).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        self._send(200, {"tools": core.TOOLS}) if self.path == "/tools" else self._send(404, core.err("unknown_id", "Percorso sconosciuto."))

    def do_POST(self):
        if not self.path.startswith("/tools/"): return self._send(404, core.err("unknown_id", "Percorso sconosciuto."))
        try: args = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except (ValueError, json.JSONDecodeError): return self._send(400, core.err("invalid_params", "Corpo JSON non valido."))
        r = core.run_tool(self.path[7:], args); self._send(200 if "error" not in r else 422, r)


def serve(port=8792): ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()   # ponytail: un solo processo, nessuna coda; per più utenti serve un job runner


if __name__ == "__main__": serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8792)
