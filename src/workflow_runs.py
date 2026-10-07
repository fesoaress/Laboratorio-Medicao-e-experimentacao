"""Coleta de workflow runs (issue #43), com subdivisão mensal da janela."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from .github_client import Client, iter_pages

# Seção 3 do enunciado: classificação de `conclusion`.
SUCCESS_CONCLUSIONS = {"success"}
FAILURE_CONCLUSIONS = {"failure", "timed_out", "startup_failure"}
IGNORED_CONCLUSIONS = {"cancelled", "skipped", "neutral", "action_required", "stale", "", None}


class WorkflowRunError(ValueError):
    """Run malformado ou perda de dados por teto de 1.000 resultados num mês."""


def classify_conclusion(conclusion: str | None) -> str | None:
    if conclusion in SUCCESS_CONCLUSIONS:
        return "success"
    if conclusion in FAILURE_CONCLUSIONS:
        return "failure"
    if conclusion in IGNORED_CONCLUSIONS:
        return None
    raise WorkflowRunError(f"conclusion desconhecida: {conclusion!r}.")


def month_windows(start: date, end: date) -> list[tuple[date, date]]:
    """Janelas mensais [início, fim) cobrindo [start, end), clipadas nas pontas."""
    if end <= start:
        raise WorkflowRunError("Janela inválida: end_date deve ser posterior a start_date.")
    windows = []
    cursor = start
    while cursor < end:
        if cursor.month == 12:
            next_month = cursor.replace(year=cursor.year + 1, month=1, day=1)
        else:
            next_month = cursor.replace(month=cursor.month + 1, day=1)
        windows.append((cursor, min(next_month, end)))
        cursor = next_month
    return windows


def parse_workflow_run(run: dict[str, Any], default_branch: str) -> dict[str, Any] | None:
    """Valida um run bruto; retorna None se não for push no default branch."""
    try:
        identifier = run["id"]
        workflow_id = run["workflow_id"]
        branch = run["head_branch"]
        event = run["event"]
        conclusion = run.get("conclusion")
        created_at = run["created_at"]
        run_started_at = run["run_started_at"]
        updated_at = run["updated_at"]
        if type(identifier) is not int or type(workflow_id) is not int:
            raise WorkflowRunError("id ou workflow_id inválido.")
        for value in (created_at, run_started_at, updated_at):
            if not isinstance(value, str) or not value.strip():
                raise WorkflowRunError("Timestamp de run ausente ou inválido.")
    except KeyError as error:
        raise WorkflowRunError("Campo obrigatório ausente no workflow run.") from error
    if branch != default_branch or event != "push":
        return None  # defesa extra; a API já deveria ter filtrado isto
    return {
        "id": identifier,
        "workflow_id": workflow_id,
        "head_branch": branch,
        "event": event,
        "conclusion": conclusion,
        "status_class": classify_conclusion(conclusion),
        "created_at": created_at,
        "run_started_at": run_started_at,
        "updated_at": updated_at,
    }


@dataclass(frozen=True)
class MonthReport:
    start: str
    end: str
    total_count: int
    items_seen: int
    capped: bool


def collect_workflow_runs(
    client: Client, full_name: str, default_branch: str,
    start_date: str, end_date: str, *, per_page: int = 100,
) -> tuple[list[dict[str, Any]], list[MonthReport]]:
    """Coleta runs push/default_branch na janela, mês a mês.

    Levanta WorkflowRunError se algum mês individual tiver mais de 1.000
    resultados: nesse caso a API não entrega tudo via paginação e os dados
    faltantes não devem ser silenciosamente ignorados nem contados como 0.
    """
    window_start = date.fromisoformat(start_date)
    window_end = date.fromisoformat(end_date)
    runs: list[dict[str, Any]] = []
    reports: list[MonthReport] = []
    for month_start, month_end in month_windows(window_start, window_end):
        # created=.. é um intervalo inclusivo nas duas pontas na API do GitHub;
        # por isso filtramos de novo no cliente contra [window_start, window_end).
        created_range = f"{month_start.isoformat()}..{month_end.isoformat()}"
        items_seen = 0
        total_count = None
        pages = iter_pages(
            client, f"/repos/{full_name}/actions/runs",
            {"branch": default_branch, "event": "push", "created": created_range, "per_page": per_page},
        )
        for response in pages:
            data = response.data
            if not isinstance(data, dict) or not isinstance(data.get("workflow_runs"), list):
                raise WorkflowRunError(f"Resposta inesperada de workflow runs para {full_name}.")
            total_count = data.get("total_count")
            if type(total_count) is not int or total_count < 0:
                raise WorkflowRunError(f"total_count inválido para {full_name}.")
            for raw_run in data["workflow_runs"]:
                items_seen += 1
                parsed = parse_workflow_run(raw_run, default_branch)
                if parsed is None:
                    continue
                run_date = datetime.fromisoformat(
                    parsed["created_at"].replace("Z", "+00:00")
                ).astimezone(timezone.utc).date()
                if window_start <= run_date < window_end:
                    runs.append(parsed)
        capped = items_seen >= 1000 and (total_count or 0) > items_seen
        if capped:
            raise WorkflowRunError(
                f"{full_name}: mês {month_start.isoformat()} tem {total_count} runs, "
                f"além do teto de 1.000 por consulta. Subdivisão semanal necessária."
            )
        reports.append(MonthReport(month_start.isoformat(), month_end.isoformat(), total_count or 0, items_seen, capped))
    return runs, reports
