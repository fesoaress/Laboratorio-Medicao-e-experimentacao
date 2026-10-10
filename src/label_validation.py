"""Valida preenchimento humano e alinhamento com a amostra cega (#54)."""

from collections import defaultdict
from pathlib import Path

from .gold_sample import CATEGORIES, CONTEXT_FIELDS, LABEL_FIELDS, read_csv, validate_sample


def load_sample(path: Path) -> dict[str, dict]:
    return validate_sample(read_csv(path, CONTEXT_FIELDS, exact=True))


def validate_labels(path: Path, sample: dict[str, dict]) -> dict:
    errors, indexed, grouped = [], {}, defaultdict(list)
    try:
        rows = read_csv(path, LABEL_FIELDS, exact=True)
    except (OSError, ValueError) as error:
        rows = []
        errors.append(str(error))
    for line, row in enumerate(rows, 2):
        identifier = row["item_id"]
        if identifier in indexed:
            errors.append(f"linha {line}: item duplicado {identifier}")
            continue
        indexed[identifier] = row
        if identifier not in sample:
            errors.append(f"linha {line}: item/repositório/release desalinhado {identifier}")
            continue
        differences = [field for field in CONTEXT_FIELDS if row[field] != sample[identifier][field]]
        if differences:
            errors.append(f"linha {line}: contexto/identidade alterado: {', '.join(differences)}")
        grouped[sample[identifier]["repository"]].append(row)
        for dimension, categories in CATEGORIES.items():
            value = row[dimension]
            if value not in categories:
                reason = "campo obrigatório vazio" if not value else f"valor inválido {value!r}"
                errors.append(f"linha {line}: {dimension}: {reason}")
    missing = sorted(set(sample) - set(indexed))
    if missing:
        errors.append(f"{len(missing)} itens ausentes: {', '.join(missing)}")
    evaluated_repositories = 0
    for name in sorted({row["repository"] for row in sample.values()}):
        items = grouped[name]
        consistent = True
        for dimension in ("project_type", "releases_represent_real_delivery"):
            values = {row[dimension] for row in items}
            if len(values) > 1:
                errors.append(f"{name}: {dimension} inconsistente nas 5 linhas do repositório")
            if len(values) != 1 or not values.issubset(CATEGORIES[dimension]):
                consistent = False
        if len(items) == 5 and consistent:
            evaluated_repositories += 1
    evaluated_releases = sum(row["corrective_release"] in CATEGORIES["corrective_release"]
                              for key, row in indexed.items() if key in sample)
    return {"file": str(path), "complete": not errors,
            "repositories_evaluated": evaluated_repositories,
            "repositories_missing": 60 - evaluated_repositories,
            "releases_evaluated": evaluated_releases,
            "releases_missing": len(sample) - evaluated_releases,
            "errors": errors, "rows": indexed}


def public_result(result: dict) -> dict:
    return {key: value for key, value in result.items() if key != "rows"}
