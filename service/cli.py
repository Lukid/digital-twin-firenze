#!/usr/bin/env python3
"""CLI: python service/cli.py <strumento> '<json argomenti>' | list | replay <job_id>. Stesso nucleo di API e MCP."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import core


def main(argv):
    if not argv or argv[0] in ("-h", "--help"): print(__doc__ + "\nStrumenti: " + ", ".join(core.TOOLS)); return 0
    if argv[0] == "replay":
        import replay
        r = replay.replay(argv[1]); print(json.dumps(r, ensure_ascii=False, indent=1)); return 0 if r.get("match") else 1
    try: args = json.loads(argv[1]) if len(argv) > 1 else {}
    except json.JSONDecodeError as e: print(f"JSON non valido: {e}", file=sys.stderr); return 2
    r = core.run_tool(argv[0], args); print(json.dumps(r, ensure_ascii=False, indent=1)); return 1 if "error" in r else 0


if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
