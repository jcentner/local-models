#!/usr/bin/env python3
"""Local benchmark-run viewer — a tiny stdlib HTTP server.

Reads the committed index (lab/benchmarks/results.csv), lazy-loads the
gitignored raw runs (lab/benchmarks/runs/*.jsonl) on demand, and serves the
wiki markdown read-only. No third-party deps, no build step.

    python3 server.py [--port 8777] [--host 127.0.0.1]
    open http://127.0.0.1:8777

Read-only: only GET is handled; all file access is confined to known dirs.
"""
from __future__ import annotations

import argparse
import csv
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
RESULTS_CSV = REPO_ROOT / "lab" / "benchmarks" / "results.csv"
RUNS_DIR = REPO_ROOT / "lab" / "benchmarks" / "runs"
WIKI_DIR = REPO_ROOT / "wiki"

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def _safe_child(base: Path, rel: str) -> Path | None:
    """Resolve ``rel`` under ``base``; return None if it escapes ``base``."""
    candidate = (base / rel).resolve()
    base = base.resolve()
    if candidate == base or base in candidate.parents:
        return candidate
    return None


def load_runs() -> list[dict]:
    if not RESULTS_CSV.exists():
        return []
    with RESULTS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        raw = (r.get("raw_file") or "").strip()
        r["raw_exists"] = bool(raw) and (RUNS_DIR / raw).is_file()
    return rows


def load_run_items(filename: str) -> dict:
    # Only a bare filename within RUNS_DIR is allowed.
    if "/" in filename or "\\" in filename or not filename.endswith(".jsonl"):
        raise ValueError("invalid run filename")
    path = RUNS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(filename)
    items, errors = [], 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                errors += 1
    return {"file": filename, "n_items": len(items), "parse_errors": errors, "items": items}


def list_wiki() -> list[str]:
    if not WIKI_DIR.is_dir():
        return []
    return sorted(
        str(p.relative_to(WIKI_DIR)) for p in WIKI_DIR.rglob("*.md")
    )


def read_wiki(rel: str) -> str:
    if not rel.endswith(".md"):
        raise ValueError("not a markdown file")
    path = _safe_child(WIKI_DIR, rel)
    if path is None or not path.is_file():
        raise FileNotFoundError(rel)
    return path.read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "RunViewer/1.0"

    def log_message(self, fmt, *args):  # quieter console
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, content_type="text/plain; charset=utf-8", status=200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, name, content_type):
        path = HERE / name
        if not path.is_file():
            self._send_text("Not found", status=404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path, qs = parsed.path, parse_qs(parsed.query)

        if path in STATIC_FILES:
            name, ct = STATIC_FILES[path]
            self._send_static(name, ct)
            return

        if path == "/api/runs":
            self._send_json({"runs": load_runs()})
            return

        if path == "/api/run":
            fname = (qs.get("file") or [""])[0]
            try:
                self._send_json(load_run_items(fname))
            except FileNotFoundError:
                self._send_json({"error": "run file not found", "file": fname}, status=404)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
            return

        if path == "/api/wiki":
            rel = (qs.get("path") or [""])[0]
            if not rel:
                self._send_json({"files": list_wiki()})
                return
            try:
                self._send_text(read_wiki(rel), content_type="text/markdown; charset=utf-8")
            except FileNotFoundError:
                self._send_json({"error": "wiki file not found", "path": rel}, status=404)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
            return

        self._send_text("Not found", status=404)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8777)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    mimetypes.add_type("text/javascript", ".js")
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"run-viewer → http://{args.host}:{args.port}  (repo: {REPO_ROOT})")
    print(f"  results.csv: {'ok' if RESULTS_CSV.exists() else 'MISSING'} · "
          f"runs/: {len(list(RUNS_DIR.glob('*.jsonl'))) if RUNS_DIR.is_dir() else 0} files · "
          f"wiki/: {len(list_wiki())} md")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
