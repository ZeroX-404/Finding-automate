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

## V1.5 Independent Critic

V1.5 adds a separate ledger-only critic stage. The critic does not read repository
files, execute scanners, create a Validation, or create/promote a Finding.

```text
ContextAssessment
      ↓
Independent Critic
      ├── objections
      ├── missing evidence
      ├── alternative explanations
      └── verdict
```

Verdicts are epistemic, not vulnerability states:

- `SUPPORTS`: keep investigating; no deterministic falsifier survived the current review.
- `CHALLENGES`: material counterpoint exists and must be resolved.
- `REJECTS`: current deterministic evidence satisfies a falsifier for this hypothesis/snapshot.
- `INCONCLUSIVE`: evidence is insufficient for the critic to decide.

Run the acceptance corpus:

```bash
research-agent critic-case --db critic-evidence.db --repo-commit "$(git rev-parse HEAD)"
```

Review one assessment:

```bash
research-agent criticize-context CAS-xxxxxxxxxxxx --db signal-evidence.db
```

## V1.6 ResearchModel interface and proposal boundary

V1.6 introduces the first model-facing research harness, but intentionally ships
with an offline deterministic `MockResearchModel` only. A model cannot create a
Hypothesis, Claim, Validation, or Finding. Its durable output is a
`ResearchProposal` (`PRP-*`) that must pass a strict Pydantic schema.

```text
validated ledger context
        ↓
ResearchPacket
  trusted_contract
  +
  untrusted_repository_data
        ↓
ResearchModel
        ↓
ModelProposalOutput schema gate
        ↓
ResearchProposal
```

Repository content is explicitly delimited as untrusted data. Prompt-like text in
comments or source files cannot modify the trusted contract, capabilities, or
ledger permissions. Extra model fields are rejected instead of silently ignored,
so a model cannot smuggle fields such as `finding_state=CONFIRMED` through the
proposal channel.

Run the offline acceptance corpus:

```bash
rm -f researcher-evidence.db
research-agent researcher-case --db researcher-evidence.db --repo-commit "$(git rev-parse HEAD)"
```

Generate one proposal from an existing contextual assessment and critic record:

```bash
research-agent research-propose \
  CAS-... \
  CRT-... \
  targets/contextual_validator_cases \
  --db critic-evidence.db \
  --model mock-v1.6
```

V1.6 acceptance requires zero `Claim`, `Validation`, or `Finding` objects created
by the researcher stage, a clean ledger audit, source-snapshot integrity, and a
preserved repository-content-as-data boundary.

## V1.7 Proposal Promotion Gate

V1.7 adds a deterministic firewall between model-authored `ResearchProposal`
objects and durable research state.

```text
ResearchProposal
      ↓
Proposal Gate
      ├─ lineage/provenance
      ├─ scope + commit freshness
      ├─ critic/assessment state
      ├─ duplicate check
      ├─ unsupported certainty check
      └─ trust-boundary preservation
             ↓
      ACCEPT / REJECT / DEFER
```

Only `ACCEPT` for a `HYPOTHESIS_REFINEMENT` may create a new `Hypothesis`.
Evidence requests are always deferred to a future scoped executor. The gate
never creates `Claim`, `Validation`, or `Finding` objects and never executes
repository, network, or shell tools.

```bash
research-agent gate-proposal PRP-... --db evidence.db
research-agent promotion-case --db promotion-evidence.db
```

## V1.8 OpenAI-compatible model adapter and runtime workspace

V1.8 adds the first real HTTP model adapter while keeping acceptance completely
offline. Runtime state is anchored to `.research-agent/` under the project root,
so default databases no longer depend on the shell working directory.

```text
ResearchPacket
     ↓
OpenAICompatibleResearchModel
     ├─ explicit endpoint/model
     ├─ no tools
     ├─ timeout
     ├─ request-size ceiling
     ├─ response-size ceiling
     ├─ no HTTP redirects
     ├─ raw/fenced JSON only
     └─ strict ModelProposalOutput schema
             ↓
       ResearchProposal
```

The default policy contains `model:invoke: DENY`. A real endpoint call is blocked
until the user explicitly changes that capability to `ALLOW`. API keys are read
only from a named environment variable and are never persisted in ledger
metadata. Safe adapter metadata records the endpoint origin plus SHA-256 hashes
of the raw HTTP request/response for traceability.

Show the runtime workspace:

```bash
research-agent runtime-info
```

Run the fully offline HTTP-adapter acceptance case:

```bash
research-agent compatible-case --repo-commit "$(git rev-parse HEAD)"
```

After explicitly authorizing `model:invoke`, invoke a configured compatible
endpoint:

```bash
export RESEARCH_MODEL_API_KEY='...'
research-agent research-propose-compatible \
  CAS-... CRT-... targets/contextual_validator_cases \
  my-model http://127.0.0.1:8000/v1 \
  --api-key-env RESEARCH_MODEL_API_KEY \
  --repo-commit "$(git rev-parse HEAD)"
```

V1.8 uses the Chat Completions compatibility surface and does not expose tool
calling to the model. Model output remains a proposal and still requires the
V1.7 promotion gate before it can affect durable hypothesis state.


## V1.9 Evidence Request Executor

V1.9 introduces a deterministic executor for `EVIDENCE_REQUEST` proposals that were explicitly deferred by the V1.7 proposal gate. The executor is intentionally not a shell and does not accept arbitrary commands from a model.

Execution boundary:

```text
ResearchProposal (SEEK_EVIDENCE)
        |
ProposalDecision (DEFER)
        |
        v
Evidence Request Executor
        |
        +-- closed operation registry
        +-- repository scope check
        +-- source snapshot check
        +-- bounded Python AST parsing
        +-- no network
        +-- no shell/subprocess
        +-- no repository writes
        |
        v
Method -> Experiment -> Evidence (NEUTRAL)
```

Approved V1.9 operations are `SOURCE_CONTEXT`, `CALL_SITE_SEARCH`, `SYMBOL_REFERENCE_SEARCH`, `INTERPROCEDURAL_TRACE`, and `GUARD_ANALYSIS`. Unsupported natural-language requests are not mapped to a generic fallback.

The executor only records syntactic facts. Its evidence is always `NEUTRAL`; it cannot create `Claim`, `Validation`, or `Finding`, and it cannot assert attacker control, exploitability, or safety. New evidence must flow back through validation and criticism before research state changes.

Run the offline acceptance case:

```bash
research-agent executor-case --repo-commit "$(git rev-parse HEAD)"
```
