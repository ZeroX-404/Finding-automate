# Security Research Workflow V1

## Objective

Investigate authorized local source code using falsifiable hypotheses and auditable evidence.

## Workflow

1. Record observations.
2. Create a hypothesis.
3. State a falsifier.
4. State a prediction.
5. Select the least-privileged analysis method.
6. Collect evidence.
7. Record both supporting and contradictory evidence.
8. Send the candidate to an independent critic.
9. Prefer deterministic validation over model judgment.
10. Promote to CONFIRMED only after the finding gate accepts required validation.

## Researcher constraints

- Scanner output is an observation, not a finding.
- Model confidence is not verification.
- Do not suppress contradictory evidence.
- Do not infer a CVE identifier.
- CWE mapping requires root-cause reasoning.
- External target interaction is outside V1.

## Critic role

The critic must search for:
- unsupported assumptions,
- missing data-flow edges,
- hidden sanitization,
- unreachable paths,
- configuration dependencies,
- benign alternative explanations,
- evidence that would falsify the claim.

The critic cannot promote a candidate to CONFIRMED.
