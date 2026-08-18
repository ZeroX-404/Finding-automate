from __future__ import annotations

import json

import typer

from .adapters.codeql_sarif import observations_from_sarif
from .adapters.semgrep import observations_from_semgrep
from .ledger import Ledger
from .policy import ScopePolicy
from .synthetic_case import run_synthetic_case

app = typer.Typer(no_args_is_help=True)


@app.command("init-db")
def init_db(db: str = "evidence.db") -> None:
    ledger = Ledger(db)
    ledger.init()
    typer.echo(f"Initialized {db}")


@app.command("show-policy")
def show_policy(path: str = "policy/scope.yaml") -> None:
    policy = ScopePolicy.load(path)
    typer.echo(json.dumps(policy.model_dump(mode="json"), indent=2))


@app.command("ingest-semgrep")
def ingest_semgrep(
    json_path: str,
    db: str = "evidence.db",
    repo_commit: str | None = None,
) -> None:
    ledger = Ledger(db)
    ledger.init()
    observations = observations_from_semgrep(json_path, repo_commit)
    for obs in observations:
        ledger.put(obs)
    typer.echo(f"Ingested {len(observations)} Semgrep observations.")


@app.command("ingest-sarif")
def ingest_sarif(
    sarif_path: str,
    db: str = "evidence.db",
    repo_commit: str | None = None,
) -> None:
    ledger = Ledger(db)
    ledger.init()
    observations = observations_from_sarif(sarif_path, repo_commit)
    for obs in observations:
        ledger.put(obs)
    typer.echo(f"Ingested {len(observations)} SARIF observations.")


@app.command("explain")
def explain(
    object_id: str,
    db: str = "evidence.db",
    max_depth: int = 4,
) -> None:
    ledger = Ledger(db)
    ledger.init()

    try:
        result = ledger.trace(object_id, max_depth=max_depth)
    except KeyError:
        typer.echo(
            f"Error: object '{object_id}' not found in {db}",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(json.dumps(result, indent=2))

@app.command("history")
def history(object_id: str, db: str = "evidence.db") -> None:
    ledger = Ledger(db)
    ledger.init()
    typer.echo(json.dumps(ledger.history(object_id), indent=2))


@app.command("audit-ledger")
def audit_ledger(db: str = "evidence.db") -> None:
    ledger = Ledger(db)
    ledger.init()
    result = ledger.audit()
    typer.echo(json.dumps(result, indent=2))
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("synthetic-case")
def synthetic_case(db: str = "evidence.db") -> None:
    """Run the local-only end-to-end acceptance research case."""
    ledger = Ledger(db)
    result = run_synthetic_case(ledger)
    typer.echo(json.dumps(result, indent=2))
