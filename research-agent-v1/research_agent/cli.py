from __future__ import annotations

import json
from pathlib import Path

import typer

from .adapters.codeql_sarif import observations_from_sarif
from .adapters.semgrep import observations_from_semgrep
from .ledger import Ledger
from .policy import ScopePolicy

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
def explain(object_id: str, db: str = "evidence.db") -> None:
    ledger = Ledger(db)
    typer.echo(json.dumps(ledger.graph(object_id), indent=2))
