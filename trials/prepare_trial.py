"""Cria uma cópia isolada e rastreável de um kata para um trial da S02."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    FERNANDA_ALLOCATION,
    ISLAYDER_ALLOCATION,
    KATAS_DIR,
    TRIALS_CSV,
    WORKSPACES_DIR,
)


class PreparationError(ValueError):
    """Entrada inválida ou risco de sobrescrever um trial existente."""


def normalize_treatment(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in {"ia", "ai"}:
        return "IA"
    if normalized == "manual":
        return "Manual"
    raise PreparationError("Tratamento inválido. Use IA ou Manual.")


def normalize_issue(value: str) -> str:
    number = value.strip().removeprefix("#")
    if not number.isdigit() or int(number) <= 0:
        raise PreparationError("Issue inválida. Informe o número, por exemplo: 23.")
    return f"#{int(number)}"


def safe_slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", ascii_value).strip("-_").lower()
    if not slug:
        raise PreparationError("Participante não pode ficar vazio.")
    return slug


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def available_katas(katas_dir: Path = KATAS_DIR) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.name
            for path in katas_dir.iterdir()
            if path.is_dir()
            and path.name.startswith("kata")
            and (path / "solucao.py").is_file()
            and (path / "test_solucao.py").is_file()
        )
    )


def ensure_issue_unused(issue: str, workspaces_dir: Path, trials_csv: Path) -> None:
    if workspaces_dir.exists():
        for manifest_path in workspaces_dir.rglob("trial.json"):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PreparationError(
                    f"Manifesto existente inválido; revise antes de preparar outro trial: "
                    f"{manifest_path}: {exc}"
                ) from exc
            if manifest.get("issue") == issue:
                raise PreparationError(
                    f"A Issue {issue} já está vinculada ao workspace {manifest_path.parent}. "
                    "Cada trial precisa de uma Issue individual."
                )

    if trials_csv.exists():
        try:
            with trials_csv.open(newline="", encoding="utf-8-sig") as handle:
                for row in csv.DictReader(handle):
                    if row.get("issue") == issue:
                        raise PreparationError(
                            f"A Issue {issue} já aparece em {trials_csv}. "
                            "Uma repetição exige outra Issue."
                        )
        except (OSError, csv.Error) as exc:
            raise PreparationError(
                f"Não foi possível verificar as Issues em {trials_csv}: {exc}"
            ) from exc


def prepare_trial(
    participant: str,
    kata: str,
    treatment: str,
    issue: str,
    *,
    katas_dir: Path = KATAS_DIR,
    workspaces_dir: Path = WORKSPACES_DIR,
    trials_csv: Path = TRIALS_CSV,
) -> Path:
    participant = participant.strip()
    if not participant:
        raise PreparationError("Participante não pode ficar vazio.")

    treatment = normalize_treatment(treatment)
    issue = normalize_issue(issue)
    katas = available_katas(katas_dir)
    if kata not in katas:
        choices = ", ".join(katas) or "nenhum kata encontrado"
        raise PreparationError(f"Kata inválido: {kata!r}. Disponíveis: {choices}.")

    allocation_by_participant = {
        "islayder": ISLAYDER_ALLOCATION,
        "fernanda": FERNANDA_ALLOCATION,
    }
    expected = allocation_by_participant.get(participant.casefold(), {}).get(kata)
    if expected is not None and expected != treatment:
        raise PreparationError(
            f"Alocação de {participant} para {kata}: {expected}; recebido: {treatment}."
        )

    participant_slug = safe_slug(participant)
    issue_number = issue.removeprefix("#")
    workspace = (
        workspaces_dir
        / participant_slug
        / f"{kata}_{treatment.casefold()}_issue-{issue_number}"
    )
    if workspace.exists():
        raise PreparationError(
            f"Workspace já existe e não será sobrescrito: {workspace}\n"
            "Use a pasta existente ou crie uma nova Issue para uma repetição válida."
        )
    ensure_issue_unused(issue, workspaces_dir, trials_csv)

    source = katas_dir / kata
    workspace.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{workspace.name}-", dir=workspace.parent))
    try:
        for filename in ("solucao.py", "test_solucao.py"):
            shutil.copy2(source / filename, temporary / filename)

        manifest = {
            "schema_version": 1,
            "participant": participant,
            "kata": kata,
            "treatment": treatment,
            "issue": issue,
            "status": "prepared",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_path": source.resolve().as_posix(),
            "solution_initial_sha256": sha256(temporary / "solucao.py"),
            "test_sha256": sha256(temporary / "test_solucao.py"),
        }
        (temporary / "trial.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, workspace)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return workspace


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepara workspace isolado de um trial.")
    parser.add_argument("--participant", required=True)
    parser.add_argument("--kata", required=True, choices=available_katas())
    parser.add_argument("--treatment", required=True, help="IA ou Manual")
    parser.add_argument("--issue", required=True, help="Número da Issue do trial")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        workspace = prepare_trial(
            args.participant, args.kata, args.treatment, args.issue
        )
    except PreparationError as exc:
        print(f"ERRO: {exc}")
        return 1
    print(f"Workspace preparado: {workspace}")
    print("Abra somente essa pasta no editor durante o trial.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
