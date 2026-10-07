"""Liga workflow runs + CFR(a) + tempo de recuperação ao pipeline (#46).

Uso opcional: quando a janela oficial (config.start_date/end_date) está
definida, esta função substitui a necessidade do --validation-csv manual
para valid_workflow_runs, coletando o dado real via API em vez de depender
de uma planilha fornecida à parte.
"""

from __future__ import annotations

from typing import Any

from .cache import ResilientClient
from .config import SelectionConfig
from .metrics import change_failure_rate_a, recovery_episodes, repository_recovery_time
from .workflow_runs import WorkflowRunError, collect_workflow_runs


def collect_workflow_metrics(client: ResilientClient, row: dict[str, Any], config: SelectionConfig) -> dict[str, Any]:
    """Para um repositório já com metadata_complete e has_github_actions=True."""
    if not config.start_date or not config.end_date:
        raise ValueError("Janela oficial ausente; não é possível coletar workflow runs.")
    runs, month_reports = collect_workflow_runs(
        client, row["full_name"], row["default_branch"], config.start_date, config.end_date,
    )
    cfr = change_failure_rate_a(runs)
    recovery = repository_recovery_time(recovery_episodes(runs))
    return {
        "valid_workflow_runs": len(runs),
        "cfr_a": cfr.cfr,
        "cfr_a_successes": cfr.successes,
        "cfr_a_failures": cfr.failures,
        "cfr_a_ignored": cfr.ignored,
        "recovery_time_median_hours": recovery.median_hours,
        "recovery_time_n_episodes": recovery.n_episodes,
        "recovery_time_censored_proportion": recovery.censored_proportion,
        "workflow_runs_months": [report.__dict__ for report in month_reports],
    }
