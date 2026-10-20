"""RQ03(b): qualquer corretiva posterior em até 7 dias; censura final incondicional."""

import argparse
import json
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

from .gold_sample import boolean, read_csv, sha256, timestamp
from .pipeline import write_csv
from .temporal import ObservationWindow

POLICY = "any_corrective_7d_v1"
DEFINITION = ("Cada release estável original é falha se existe qualquer release estável com publicação "
              "estritamente posterior e em até 7 dias, classificada como corretiva pela heurística validada. "
              "Intermediárias não impedem evidência. Originais a partir de end-7d são censuradas "
              "incondicionalmente, mas podem ser evidência para anteriores. Sem corretiva positiva conhecida, "
              "qualquer classificação posterior indisponível no intervalo torna o original não calculável. "
              "Ausência de predecessora não exclui o original. Cada original conta no máximo uma vez.")


def calculate(rows: list[dict], window: ObservationWindow) -> tuple[list[dict], list[dict]]:
    """Distingue zero observado, censura e ausência de evidência calculável."""
    grouped, seen = defaultdict(list), set()
    for row in rows:
        key = row["full_name"].casefold(), row["release_id"]
        if key in seen or not window.contains(row["published_at"]):
            raise ValueError("Release duplicada ou fora da janela CFR(b).")
        if row["corrective_release"] not in ("yes", "no"):
            raise ValueError("Previsão corretiva fora do domínio.")
        boolean(str(row["classification_usable"]))
        seen.add(key)
        grouped[row["full_name"]].append(row)
    details, summaries = [], []
    cutoff = window.end - timedelta(days=7)
    for name, releases in sorted(grouped.items()):
        releases.sort(key=lambda r: (timestamp(r["published_at"]), int(r["release_id"])))
        times = [timestamp(r["published_at"]) for r in releases]
        corrective = [i for i, r in enumerate(releases) if boolean(str(r["classification_usable"])) and r["corrective_release"] == "yes"]
        unavailable = [i for i, r in enumerate(releases) if not boolean(str(r["classification_usable"]))]
        corrective_times = [times[i] for i in corrective]
        unavailable_times = [times[i] for i in unavailable]
        counts = Counter()
        for i, release in enumerate(releases):
            started = times[i]
            until = started + timedelta(days=7)
            pos = bisect_right(corrective_times, started)
            witness = corrective[pos] if pos < len(corrective) and corrective_times[pos] <= until else None
            unknown = bisect_right(unavailable_times, until) - bisect_right(unavailable_times, started)
            if started >= cutoff:
                status, failed = "right_censored", ""
            elif witness is not None:
                status, failed = "failed", "True"
            elif unknown:
                status, failed = "unassessable_context", ""
            else:
                status, failed = "not_failed", "False"
            counts[status] += 1
            details.append({"full_name": name, "release_id": release["release_id"], "tag_name": release["tag_name"],
                "published_at": release["published_at"], "has_predecessor": bool(release.get("previous_release_id")),
                "observation_end": until.isoformat(), "status": status, "failed": failed,
                "evidence_release_id": releases[witness]["release_id"] if witness is not None else "",
                "evidence_tag": releases[witness]["tag_name"] if witness is not None else "",
                "unavailable_posterior_classifications": unknown})
        denominator = counts["failed"] + counts["not_failed"]
        summaries.append({"full_name": name, "releases": len(releases), "failed_releases": counts["failed"],
            "evaluable_releases": denominator, "right_censored": counts["right_censored"],
            "unassessable_context": counts["unassessable_context"],
            "cfr_delivery": counts["failed"] / denominator if denominator else "",
            "status": "calculated" if denominator else "not_calculable_zero_evaluable_releases"})
    return summaries, details


def run(folder: Path, population_dir: Path) -> dict:
    outputs = [folder / name for name in ("cfr_delivery_s02.csv", "cfr_delivery_releases_s02.csv", "cfr_delivery_manifest_s02.json")]
    if any(p.exists() for p in outputs):
        raise ValueError("CFR(b) já existe; preserve os resultados antes de nova execução.")
    manifest_path = population_dir / "manifest.json"
    predictions_path = population_dir / "release_predictions.csv"
    population = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(predictions_path) != population["predictions_sha256"]:
        raise ValueError("Previsões diferem do manifesto da população.")
    evaluation_path = Path(population["evaluation"])
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    if (sha256(evaluation_path) != population["evaluation_sha256"] or evaluation["status"] != "accepted"
            or evaluation["f1"] < .70 or evaluation["version"] != population["version"]):
        raise ValueError("Avaliação aceita e rastreável é obrigatória.")
    for source in population["sources"]:
        if sha256(Path(source["path"])) != source["sha256"]:
            raise ValueError("Fonte da população mudou.")
    window = ObservationWindow(**population["window"])
    rows = read_csv(predictions_path)
    summaries, details = calculate(rows, window)
    repos = read_csv(folder / "repositories_final_s02.csv")
    if ({r["full_name"] for r in repos} != {r["full_name"] for r in summaries}
            or len(rows) != population["releases"] or len(summaries) != population["repositories"]):
        raise ValueError("CFR(b) não cobre a população esperada.")
    source = f"{outputs[2].as_posix()};policy={POLICY};heuristic={population['version']};evaluation_sha256={population['evaluation_sha256']}"
    for row in summaries:
        row["source"] = source
    folder.mkdir(parents=True, exist_ok=True)
    write_csv(outputs[0], tuple(summaries[0]), summaries)
    write_csv(outputs[1], tuple(details[0]), details)
    result = {"policy": POLICY, "definition": DEFINITION,
        "decision_source": "Definição operacional confirmada pelo grupo em 20/10/2026, com trechos do enunciado RQ03(b).",
        "window": population["window"], "right_censoring_cutoff": (window.end - timedelta(days=7)).isoformat(),
        "heuristic_version": population["version"], "evaluation": population["evaluation"],
        "evaluation_sha256": population["evaluation_sha256"],
        "population_manifest": manifest_path.as_posix(), "population_manifest_sha256": sha256(manifest_path),
        "predictions_sha256": sha256(predictions_path), "repositories": len(summaries),
        "valid_repositories": sum(r["cfr_delivery"] != "" for r in summaries),
        "missing_repositories": sum(r["cfr_delivery"] == "" for r in summaries),
        "release_statuses": dict(Counter(r["status"] for r in details)),
        "outputs": [{"path": p.as_posix(), "sha256": sha256(p)} for p in outputs[:2]]}
    outputs[2].write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=Path("data/processed/s02"))
    parser.add_argument("--population-dir", type=Path, default=Path("data/processed/s02/corrective_v5"))
    args = parser.parse_args(argv)
    result = run(args.folder, args.population_dir)
    print(f"CFR(b): {result['valid_repositories']} válidos; {result['missing_repositories']} ausentes; {result['release_statuses']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
