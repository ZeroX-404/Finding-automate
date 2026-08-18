# Research Agent V1

Evidence-centric research agent core for **authorized local source-code security research**.

V1 is deliberately constrained to L0-L3:

- L0: reason
- L1: read repository
- L2: static analysis
- L3: sandbox/local execution
- Network access: denied by policy
- Active target testing: denied
- Repository writes: denied
- External submission: denied

## Core invariant

> No claim without provenance.  
> No finding without evidence.  
> No confirmation without validation.  
> No action without capability.  
> No capability without scope.

## Pipeline

```text
Repository
  -> Observation
  -> Hypothesis
  -> Prediction
  -> Experiment
  -> Evidence Ledger
  -> Critic
  -> Deterministic Validator
  -> Finding Gate
  -> Confirmed / Rejected / Inconclusive
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .[dev]

research-agent init-db
research-agent show-policy
pytest
```

## Static analysis ingestion

Semgrep JSON:

```bash
semgrep scan --json --config auto ./target > artifacts/semgrep.json
research-agent ingest-semgrep artifacts/semgrep.json
```

CodeQL SARIF:

```bash
research-agent ingest-sarif artifacts/codeql.sarif
```

V1 does not execute active attacks or interact with external targets.

## End-to-end acceptance case

V1.1+ includes a repository-owned synthetic authorization fixture. It exercises the
full evidence lineage without network access or external targets:

```bash
research-agent synthetic-case --db synthetic-evidence.db
research-agent audit-ledger --db synthetic-evidence.db
# then use the returned finding_id
research-agent explain FIND-... --db synthetic-evidence.db --max-depth 8
research-agent history FIND-... --db synthetic-evidence.db
```

A successful run must produce a `CONFIRMED` synthetic finding, 3/3 deterministic
reproductions, a clean ledger audit, and a trace containing Source, Method,
Observation, Hypothesis, Experiment, Evidence, Claim, CriticRecord, Validation,
and Finding objects.
