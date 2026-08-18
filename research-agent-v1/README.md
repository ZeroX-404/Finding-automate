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

## V1.3 real signal pipeline

Semgrep output can now be converted into auditable signal candidates without promoting scanner output to a finding. The pipeline records scanner provenance, resolves source paths inside an authorized repository root, captures bounded source context, creates a falsifiable hypothesis candidate, and stores context as neutral evidence.

The pipeline deliberately does **not** create a Claim, Validation, or Finding. That promotion is reserved for later independent reasoning and validation stages.

Security invariant: scanner paths and repository contents are treated as untrusted input. The requested repository must first match `repository_roots` in `policy/scope.yaml`; path traversal, absolute paths outside that authorized repository, and symlink escapes are rejected before source context is read.

Acceptance fixture:

```bash
research-agent analyze-semgrep targets/semgrep_signal_target/semgrep.json targets/semgrep_signal_target --db signal-evidence.db
```

## V1.4 contextual validator

V1.4 adds deterministic Python AST interpretation for Semgrep `eval()` signals. It does not classify code as safe or vulnerable. Instead it records auditable facts and returns one of four bounded assessments:

- `SUSPICIOUS`: parameter-derived input reaches the sink with no syntactic guard candidate detected.
- `WEAKENED`: deterministic contradictory evidence exists, such as constant input or a literal-unreachable branch.
- `INCONCLUSIVE`: evidence is mixed or the validator cannot resolve security semantics.
- `NO_MATCH`: the current source snapshot does not contain the scanner-reported sink at that location.

Guard detection is intentionally non-authoritative. A syntactic guard is stored as a `GUARD_CANDIDATE` with `semantics_proven=false`; it never marks code safe by itself.

The validator verifies the source content hash recorded during signal ingestion before analysis. If the repository file changed after the scanner signal was recorded, validation stops and requires re-ingestion rather than laundering stale evidence into a new conclusion.

Run the local acceptance corpus:

```bash
rm -f contextual-evidence.db
research-agent contextual-case --db contextual-evidence.db
```

The corpus covers direct parameter flow, constant input, a guard candidate, one-hop indirect flow, a literal-unreachable branch, a stale/false scanner signal, and hostile repository comments. A passing run requires all expected assessments, a clean ledger audit, and zero `Claim`, `Validation`, or `Finding` objects.

Validate one hypothesis produced by V1.3:

```bash
research-agent validate-context HYP-... targets/my_repo --db signal-evidence.db
```
