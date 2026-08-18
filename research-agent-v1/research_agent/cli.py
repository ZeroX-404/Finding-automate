from __future__ import annotations

import json
from pathlib import Path

import typer

from .adapters.codeql_sarif import observations_from_sarif
from .adapters.semgrep import observations_from_semgrep
from .ledger import Ledger
from .policy import ScopePolicy
from .synthetic_case import run_synthetic_case
from .signal_pipeline import SignalPipelineError, run_semgrep_signal_pipeline
from .context_validator import ContextValidationError, run_python_contextual_validator
from .contextual_case import run_contextual_acceptance_case

app = typer.Typer(no_args_is_help=True)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = PROJECT_ROOT / "policy" / "scope.yaml"


@app.command("init-db")
def init_db(db: str = "evidence.db") -> None:
    ledger = Ledger(db)
    ledger.init()
    typer.echo(f"Initialized {db}")


@app.command("show-policy")
def show_policy(path: str = str(DEFAULT_POLICY_PATH)) -> None:
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


@app.command("analyze-semgrep")
def analyze_semgrep(
    json_path: str,
    repo_root: str,
    db: str = "evidence.db",
    policy_path: str = str(DEFAULT_POLICY_PATH),
    repo_commit: str | None = None,
    context_radius: int = 4,
) -> None:
    """Turn Semgrep JSON into observations, bounded context, and hypothesis candidates."""
    ledger = Ledger(db)
    try:
        policy = ScopePolicy.load(policy_path)
        result = run_semgrep_signal_pipeline(
            ledger,
            json_path,
            repo_root,
            policy=policy,
            repo_commit=repo_commit,
            context_radius=context_radius,
        )
    except (FileNotFoundError, PermissionError, SignalPipelineError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(result, indent=2))


@app.command("validate-context")
def validate_context(
    hypothesis_id: str,
    repo_root: str,
    db: str = "evidence.db",
    policy_path: str = str(DEFAULT_POLICY_PATH),
    repo_commit: str | None = None,
) -> None:
    """Deterministically assess one Python scanner hypothesis using AST evidence."""
    ledger = Ledger(db)
    try:
        policy = ScopePolicy.load(policy_path)
        result = run_python_contextual_validator(
            ledger,
            hypothesis_id,
            repo_root,
            policy=policy,
            repo_commit=repo_commit,
        )
    except (FileNotFoundError, PermissionError, ContextValidationError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(result, indent=2))


@app.command("contextual-case")
def contextual_case(
    db: str = "contextual-evidence.db",
    policy_path: str = str(DEFAULT_POLICY_PATH),
    repo_commit: str | None = None,
) -> None:
    """Run the local V1.4 contextual-validator acceptance corpus."""
    project_root = Path(__file__).resolve().parents[1]
    repo_root = project_root / "targets" / "contextual_validator_cases"
    semgrep_json = repo_root / "signals.json"
    ledger = Ledger(db)
    try:
        policy = ScopePolicy.load(policy_path)
        result = run_contextual_acceptance_case(
            ledger,
            repo_root,
            semgrep_json,
            policy=policy,
            repo_commit=repo_commit,
        )
    except (FileNotFoundError, PermissionError, ContextValidationError, SignalPipelineError, ValueError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(result, indent=2))
    if not result["all_expected"] or result["prohibited_objects"] or not result["audit"]["ok"]:
        raise typer.Exit(code=1)
