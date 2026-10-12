"""Revisão humana local da #55; nunca importa a heurística nem outros avaliadores."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import secrets
import tempfile
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import parse_qs, urlsplit

from .gold_sample import CATEGORIES, CONTEXT_FIELDS, HUMAN_FIELDS, LABEL_FIELDS, read_csv, sha256
from .label_validation import load_sample, public_result, validate_labels


class ReviewStore:
    """Só aceita decisões explícitas; salva uma cópia de segurança antes de editar."""

    def __init__(self, sample_path: Path, labels_path: Path, backup_dir: Path):
        if labels_path.name != "gold_sample_fernanda.csv":
            raise ValueError("Este formulário só abre gold_sample_fernanda.csv.")
        self.sample = load_sample(sample_path)
        self.sample_path, self.labels_path, self.backup_dir = sample_path, labels_path, backup_dir
        self.sample_revision = sha256(sample_path)
        self.lock = RLock()
        self.rows = read_csv(labels_path, LABEL_FIELDS, exact=True)
        indexed = {row["item_id"]: row for row in self.rows}
        if len(indexed) != len(self.rows) or set(indexed) != set(self.sample):
            raise ValueError("IDs do CSV individual não coincidem com a amostra.")
        for row in self.rows:
            if any(row[key] != self.sample[row["item_id"]][key] for key in CONTEXT_FIELDS):
                raise ValueError("Contexto canônico alterado; restaure antes de rotular.")
            if any(row[key] and row[key] not in allowed for key, allowed in CATEGORIES.items()):
                raise ValueError("Categoria inválida no CSV individual.")
        self.grouped = defaultdict(list)
        for row in self.rows:
            self.grouped[row["repository"]].append(row)
        self.names = sorted(self.grouped, key=str.casefold)
        self.revision = sha256(labels_path)

    def progress(self) -> dict:
        result = []
        for name in self.names:
            rows = self.grouped[name]
            decisions = sum(len({r[key] for r in rows}) == 1 and rows[0][key] in CATEGORIES[key]
                            for key in ("project_type", "releases_represent_real_delivery"))
            decisions += sum(r["corrective_release"] in CATEGORIES["corrective_release"] for r in rows)
            result.append({"repository": name, "decisions": decisions, "total": len(rows) + 2})
        return {"repositories": result, "decisions": sum(r["decisions"] for r in result),
                "total": sum(r["total"] for r in result), "revision": self.revision}

    def repository(self, index: int) -> dict:
        if index < 0 or index >= len(self.names):
            raise ValueError("Repositório fora da amostra.")
        rows = self.grouped[self.names[index]]
        # Somente fatos canônicos e rótulos armazenados no arquivo individual.
        fields = {}
        for key in ("project_type", "releases_represent_real_delivery"):
            values = {r[key] for r in rows}
            fields[key] = rows[0][key] if len(values) == 1 else ""
        return {"index": index, "repository": self.names[index], "fields": fields,
                "releases": [dict(row) for row in rows], "revision": self.revision}

    def update(self, payload: dict) -> dict:
        with self.lock:
            if (payload.get("revision") != self.revision or sha256(self.labels_path) != self.revision
                    or sha256(self.sample_path) != self.sample_revision):
                raise ValueError("CSV mudou em outra janela. Reinicie a revisão para recarregar.")
            name = payload.get("repository")
            if not isinstance(name, str) or name not in self.grouped or set(payload) != {"revision", "repository", "fields", "releases"}:
                raise ValueError("Repositório ou campos de atualização inválidos.")
            fields = payload["fields"]
            releases = payload["releases"]
            if not isinstance(fields, dict) or set(fields) != {"project_type", "releases_represent_real_delivery"}:
                raise ValueError("Informe os dois campos humanos de repositório.")
            expected = {r["item_id"] for r in self.grouped[name]}
            if not isinstance(releases, dict) or set(releases) != expected:
                raise ValueError("Informe exatamente as cinco releases sorteadas.")
            changes = {}
            for identifier, values in releases.items():
                if not isinstance(values, dict) or set(values) != {"corrective_release", "notes"}:
                    raise ValueError("Só corrective_release e notes podem ser editados por release.")
                changes[identifier] = {**fields, **values}
                for key, value in changes[identifier].items():
                    if not isinstance(value, str) or (key in CATEGORIES and value and value not in CATEGORIES[key]):
                        raise ValueError(f"Valor humano inválido para {key}.")
            updated = [{**row, **changes.get(row["item_id"], {})} for row in self.rows]
            original = self.labels_path.read_bytes()
            if hashlib.sha256(original).hexdigest() != self.revision:
                raise ValueError("CSV mudou durante o salvamento. Reinicie a revisão.")
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup = self.backup_dir / f"fernanda_{self.revision}.csv"
            if not backup.exists():
                backup.write_bytes(original)
            descriptor, temporary = tempfile.mkstemp(prefix=".fernanda-", suffix=".csv", dir=self.labels_path.parent)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8-sig", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=LABEL_FIELDS)
                    writer.writeheader()
                    writer.writerows(updated)
                    handle.flush()
                    os.fsync(handle.fileno())
                if sha256(self.labels_path) != self.revision:
                    raise ValueError("CSV mudou durante o salvamento. Reinicie a revisão.")
                os.replace(temporary, self.labels_path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            for old, new in zip(self.rows, updated):
                old.update({key: new[key] for key in HUMAN_FIELDS})
            self.revision = sha256(self.labels_path)
            return self.progress()

    def validation(self) -> dict:
        return public_result(validate_labels(self.labels_path, self.sample))


def make_server(store: ReviewStore, port: int = 8765) -> ThreadingHTTPServer:
    token = secrets.token_urlsafe(32)
    page = Path(__file__).with_name("fernanda_review.html").read_text(encoding="utf-8")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, content, kind="application/json"):
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{kind}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                return self.send(403, json.dumps({"error": "Endereço local inválido."}))
            url = urlsplit(self.path)
            try:
                with store.lock:
                    if url.path == "/":
                        return self.send(200, page.replace("__SESSION_TOKEN__", token), "text/html")
                    if url.path == "/api/progress":
                        result = store.progress()
                    elif url.path == "/api/repository":
                        result = store.repository(int(parse_qs(url.query).get("index", ["0"])[0]))
                    elif url.path == "/api/validate":
                        result = store.validation()
                    else:
                        return self.send(404, json.dumps({"error": "Página não encontrada."}))
                self.send(200, json.dumps(result, ensure_ascii=False))
            except (ValueError, OSError) as error:
                self.send(400, json.dumps({"error": str(error)}, ensure_ascii=False))

        def do_POST(self):
            origin = self.headers.get("Origin")
            expected_origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("X-Review-Token") != token or (origin and origin != expected_origin):
                return self.send(403, json.dumps({"error": "Sessão inválida."}))
            if self.path != "/api/save":
                return self.send(404, json.dumps({"error": "Página não encontrada."}))
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1_000_000:
                    raise ValueError("Tamanho da atualização inválido.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Atualização deve ser um objeto.")
                result = store.update(payload)
                self.send(200, json.dumps(result, ensure_ascii=False))
            except (ValueError, OSError) as error:
                self.send(400, json.dumps({"error": str(error)}, ensure_ascii=False))

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="#55 — rotulagem humana independente de Fernanda")
    parser.add_argument("--sample", type=Path, default=Path("data/gold_sample/gold_sample.csv"))
    parser.add_argument("--labels", type=Path, default=Path("data/gold_sample/gold_sample_fernanda.csv"))
    parser.add_argument("--backups", type=Path, default=Path("data/raw/fernanda_review_backups"))
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    store = ReviewStore(args.sample, args.labels, args.backups)
    with make_server(store, args.port) as server:
        print(f"Revisão: http://127.0.0.1:{server.server_port} — Ctrl+C para encerrar.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
