"""Auditoria reproduzível de preservação. Executar na raiz do repositório."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "main": "c4aa604ed55eec6d43a9cb5a7e126237cd1a58c2",
    "lab01": "4133fa3cbb47a2ba751e66f6399e948a421c4450",
    "lab02": "489577a7a0aaca272737464c555acef823f82cd7",
    "lab03": "3abe79b88e011bad057b4155fa56fa943c11f6f2",
    "vinicius": "3b0e0b9655442553fa95b015c52164113d738e5b",
}
ALLOWED_ADJUSTMENTS = {
    ".gitignore": "regras globais preservadas e ampliadas pelo Lab03",
    "lab01/README.md": "contexto de execução dentro de lab01 e instruções de testes",
    "lab02/README.md": "caminhos locais, instalação, testes e limitações históricas",
    "lab02/analysis/README.md": "requirements e links de relatórios",
    "lab02/analysis/analyze_rq1_rq2.py": "diretório de gráficos e resolução de caminho legado sem mudar CSV",
    "lab02/dashboard/build_dashboard.py": "docstring com caminho do gráfico",
    "lab02/reporting/build_final_report.py": "caminhos padrão do Markdown e DOCX",
    "lab02/reporting/build_template_report.py": "caminhos padrão do Markdown e DOCX",
    "lab02/reporting/qa_report.py": "caminho padrão do PDF",
    "lab02/trials/README.md": "caminho do relatório de sprint",
    "lab02/trials/config.py": "caminho dos katas",
    "lab02/trials/results/rq3_artifacts/islayder/README.md": "referência ao caminho dos katas",
    "lab02/reports/sprints/lab02_s01/vinicius.md": "referências e comando com novo caminho dos katas",
    "lab02/reports/sprints/lab02_s02/fernanda.md": "link relativo do manifesto",
    "lab02/reports/sprints/lab02_s02/islayder.md": "link relativo do manifesto",
    "lab02/reports/sprints/s03/islayder.md": "links relativos de métricas e manifesto",
    "lab02/reports/sprints/s03/relatorio_s03.md": "links relativos dos CSVs de análise",
    "lab02/reports/sprints/s03/vinicius.md": "referência ao caminho do dashboard",
    "lab03/README.md": "requirements do Lab02 e nota sobre pytest global após consolidação",
}
BINARY_SUFFIXES = {".png", ".docx", ".pdf"}
SCIENTIFIC_SUFFIXES = BINARY_SUFFIXES | {".csv", ".json"}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def tree(ref: str) -> dict[str, str]:
    result = {}
    for record in git("ls-tree", "-r", "-z", ref).split(b"\0"):
        if record:
            metadata, path = record.split(b"\t", 1)
            result[path.decode("utf-8")] = metadata.split()[2].decode("ascii")
    return result


def canonical(data: bytes, path: str) -> bytes:
    return data if Path(path).suffix in BINARY_SUFFIXES else data.replace(b"\r\n", b"\n")


def source_mapping():
    first, second = tree(SOURCES["lab01"]), tree(SOURCES["lab02"])
    for path, blob in first.items():
        yield "lab01", SOURCES["lab01"], path, "lab01/" + path, blob
    for path, blob in second.items():
        if first.get(path) == blob:
            continue  # Herança intacta pertence exclusivamente ao Lab01.
        target = path if path.startswith("lab02/") or path == ".gitignore" else "lab02/" + path
        yield "lab02", SOURCES["lab02"], path, target, blob
    for path, blob in tree(SOURCES["lab03"]).items():
        if path.startswith("lab03/"):
            yield "lab03", SOURCES["lab03"], path, path, blob


def preservation() -> tuple[list[dict], list[dict]]:
    records = []
    indexed = {}
    for record in git("ls-files", "--stage", "-z").split(b"\0"):
        if record:
            metadata, path = record.split(b"\t", 1)
            indexed[path.decode("utf-8")] = metadata.split()[1].decode("ascii")
    for lab, ref, source, target, blob in source_mapping():
        path = (ROOT / target).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise RuntimeError(f"Arquivo fonte sem correspondente: {lab}: {source}")
        original = git("cat-file", "blob", blob)
        actual = path.read_bytes()
        equal = canonical(original, source) == canonical(actual, target)
        if not equal and target not in ALLOWED_ADJUSTMENTS:
            raise RuntimeError(f"Mudança não autorizada pelo manifesto: {target}")
        if target not in indexed:
            raise RuntimeError(f"Arquivo preservado não está no índice Git: {target}")
        if Path(source).suffix in SCIENTIFIC_SUFFIXES and indexed[target] != blob:
            raise RuntimeError(f"Blob científico diferente no índice Git: {target}")
        records.append({"laboratory": lab, "source_ref": ref, "source_path": source,
            "target_path": target, "source_blob": blob,
            "target_git_blob": indexed[target], "git_blob_equal": indexed[target] == blob,
            "source_canonical_sha256": hashlib.sha256(canonical(original, source)).hexdigest(),
            "target_canonical_sha256": hashlib.sha256(canonical(actual, target)).hexdigest(),
            "bytes_equal": original == actual, "content_equal": equal, "moved": source != target,
            "adjustment": "" if equal else ALLOWED_ADJUSTMENTS[target]})
    summary = []
    for lab in ("lab01", "lab02", "lab03"):
        group = [row for row in records if row["laboratory"] == lab]
        summary.append({"laboratory": lab, "source_files": len(group), "preserved_files": len(group),
            "moved_files": sum(row["moved"] for row in group),
            "adjusted_files": sum(not row["content_equal"] for row in group), "missing_files": 0})
    return records, summary


def validate_links() -> None:
    for name in ("README.md", "lab01", "lab02", "lab03", ".github/consolidation"):
        path = ROOT / name
        documents = [path] if path.is_file() else path.rglob("*.md")
        for document in documents:
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                target = target.split("#")[0]
                if target and not (document.parent / target).exists():
                    raise RuntimeError(f"Link local ausente: {document.relative_to(ROOT)} -> {target}")


def save_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def branch_audit() -> list[dict]:
    references = {
        "main": "origin/main", "Laboratório-1": "origin/Laboratório-1",
        "Laboratorio-2": "origin/Laboratorio-2", "Laboratorio-3": "origin/Laboratorio-3",
        "vinicius": "origin/vinicius", "repo-consolidation": "HEAD",
    }
    records = []
    for name, ref in references.items():
        records.append({"branch": name, "head": git("rev-parse", ref).decode().strip(),
            "merge_base_with_main": git("merge-base", "origin/main", ref).decode().strip(),
            "exclusive_commits_vs_main": int(git("rev-list", "--count", "origin/main.." + ref)),
            "ancestor_of_consolidation": subprocess.run(
                ["git", "merge-base", "--is-ancestor", ref, "HEAD"], cwd=ROOT).returncode == 0})
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Atualiza inventários e matriz da auditoria")
    parser.add_argument("--branches", action="store_true", help="Exibe HEADs e ancestralidade atuais")
    args = parser.parse_args()
    records, summary = preservation()
    if args.write:
        directory = Path(__file__).parent
        save_csv(directory / "preservation_manifest.csv", records)
        save_csv(directory / "preservation_summary.csv", summary)
        for label, ref in SOURCES.items():
            (directory / f"tree_{label}_source.txt").write_text(
                "\n".join(tree(ref)) + "\n", encoding="utf-8", newline="\n")
        second, main_tree = tree(SOURCES["lab02"]), tree(SOURCES["main"])
        differences = [{"source_path": p, "source_blob": blob, "state": "absent" if p not in main_tree else "different"}
                       for p, blob in second.items() if main_tree.get(p) != blob]
        save_csv(directory / "lab02_changes_missing_from_main.csv", differences)
    validate_links()
    print(json.dumps(branch_audit() if args.branches else summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
