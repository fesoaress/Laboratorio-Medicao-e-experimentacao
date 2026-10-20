"""Aplica a política já validada às releases reais, sem decidir a fórmula CFR(b)."""

import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from . import corrective
from .gold_sample import boolean, read_csv, sha256, timestamp
from .pipeline import write_csv
from .temporal import ObservationWindow


def classify(folder: Path, evaluation_path: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError("Preserve a execução existente; informe outra pasta de saída.")
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    if evaluation["status"] != "accepted" or evaluation["f1"] < .70:
        raise ValueError("A política exige avaliação aceita com F1 >= 0,70.")
    implementation = Path(corrective.__file__)
    if sha256(implementation) != evaluation["implementation_sha256"]:
        # Git pode converter CRLF/LF entre Windows e Linux. Só essa diferença
        # é tolerada; o snapshot avaliado mantém seu hash bruto original.
        snapshot = evaluation_path.parent / "corrective.py.txt"
        if (not snapshot.exists() or sha256(snapshot) != evaluation["implementation_sha256"]
                or snapshot.read_bytes().replace(b"\r\n", b"\n") != implementation.read_bytes().replace(b"\r\n", b"\n")):
            raise ValueError("Implementação difere da avaliação aceita.")
    for source in evaluation["sources"]:
        if sha256(Path(source["path"].replace("\\", "/"))) != source["sha256"]:
            raise ValueError("Fonte da avaliação mudou.")
    paths = [folder / name for name in ("collection_manifest_s02.json", "repositories_final_s02.csv",
             "releases_s01.csv.gz", "release_predecessors_s02.csv", "release_intervals_s01.csv",
             "release_commits_s01.csv.gz")]
    sources = [{"path": p.as_posix(), "sha256": sha256(p)} for p in paths]
    window = ObservationWindow(**json.loads(paths[0].read_text(encoding="utf-8"))["window"])
    repos = {r["full_name"].casefold(): r for r in read_csv(paths[1])}
    history, seen = defaultdict(list), {}
    for path in paths[2:4]:
        for row in read_csv(path):
            name = row["full_name"].casefold()
            if name not in repos or boolean(row["prerelease"]):
                continue
            key = (name, row["release_id"])
            signature = row["tag_name"], timestamp(row["published_at"]), row["commit_sha"]
            if key in seen:
                if seen[key] != signature:
                    raise ValueError("Release conflitante entre histórico e predecessoras.")
                continue
            seen[key] = signature
            history[name].append(row)
    intervals = {}
    for row in read_csv(paths[4]):
        key = (row["full_name"].casefold(), row["release_id"])
        if key in intervals:
            raise ValueError("Intervalo duplicado.")
        intervals[key] = row
    messages = defaultdict(list)
    # Conserva somente assuntos necessários ao classificador, sem materializar
    # o CSV completo de commits em memória nem modificar o snapshot.
    with gzip.open(paths[5], "rt", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["full_name"].casefold(), row["release_id"])
            if key in intervals:
                messages[key].append(row["message"].splitlines()[0] if row["message"] else "")
    predictions = []
    for name in sorted(repos):
        rows = sorted(history[name], key=lambda r: (timestamp(r["published_at"]), int(r["release_id"])))
        count = 0
        for i, row in enumerate(rows):
            if not window.contains(row["published_at"]):
                continue
            count += 1
            previous = rows[i - 1] if i else None
            key = name, row["release_id"]
            interval = intervals.get(key, {})
            result = corrective.predict(tag=row["tag_name"], previous_tag=previous["tag_name"] if previous else "",
                     body=row.get("release_body", ""), messages=messages[key],
                     interval_status=interval.get("status", "missing"), version=evaluation["version"])
            note_evidence = result.correction_notes + result.feature_notes > 0
            usable = note_evidence or interval.get("status") == "complete"
            predictions.append({"full_name": repos[name]["full_name"], "release_id": row["release_id"],
                "tag_name": row["tag_name"], "published_at": row["published_at"],
                "previous_release_id": previous["release_id"] if previous else "",
                "interval_status": interval.get("status", "missing"),
                "classification_usable": usable,
                "classification_source": "notes" if note_evidence else "complete_commits" if usable else "incomplete_context",
                **result.to_dict()})
        if count != int(repos[name]["release_count"]):
            raise ValueError(f"Contagem de releases difere da amostra final: {name}")
    if any(sha256(Path(s["path"])) != s["sha256"] for s in sources):
        raise ValueError("Fontes mudaram durante a classificação.")
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "release_predictions.csv", tuple(predictions[0]), predictions)
    result = {"version": evaluation["version"], "policy": evaluation["policy"],
        "evaluation": evaluation_path.as_posix(), "evaluation_sha256": sha256(evaluation_path),
        "implementation_sha256": sha256(implementation), "sources": sources,
        "window": {"start_date": window.start_date, "end_date": window.end_date},
        "repositories": len(repos), "releases": len(predictions),
        "classification_usable": dict(Counter(str(r["classification_usable"]) for r in predictions)),
        "predictions_sha256": sha256(output / "release_predictions.csv")}
    (output / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=Path("data/processed/s02"))
    parser.add_argument("--evaluation", type=Path, default=Path("data/validation/corrective/v5/evaluation.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/s02/corrective_v5"))
    args = parser.parse_args(argv)
    result = classify(args.folder, args.evaluation, args.output_dir)
    print(f"{result['repositories']} repositórios; {result['releases']} previsões; política {result['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
