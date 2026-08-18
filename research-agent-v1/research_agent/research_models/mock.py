from __future__ import annotations

from typing import Any

from .base import ResearchPacket


class MockResearchModel:
    """Offline deterministic stand-in for a future LLM adapter.

    The mock intentionally consumes the same structured packet that a real model
    adapter will receive, but it never performs network I/O.
    """

    @property
    def model_id(self) -> str:
        return "mock-research-model-v1.6"

    def propose(self, packet: ResearchPacket) -> dict[str, Any]:
        verdict = packet.critic_verdict

        if verdict == "REJECTS":
            return {
                "schema_version": "1",
                "proposal_kind": "HYPOTHESIS_REFINEMENT",
                "disposition": "DEPRIORITIZE",
                "statement": (
                    "Do not promote the current hypothesis on the present evidence; "
                    "retain it only as a rejected research branch unless materially new evidence appears."
                ),
                "falsifier": "New independently validated evidence directly defeats the critic's rejection basis.",
                "prediction": "Without materially new evidence, deterministic review should continue to reject the current hypothesis.",
                "requested_evidence": [],
                "assumptions": [
                    "The critic reviewed the complete contextual assessment recorded in the ledger."
                ],
            }

        if verdict == "CHALLENGES":
            requested = list(packet.critic_missing_evidence) or [
                "Semantic evidence resolving the critic's challenge."
            ]
            return {
                "schema_version": "1",
                "proposal_kind": "EVIDENCE_REQUEST",
                "disposition": "SEEK_EVIDENCE",
                "statement": "The hypothesis remains unresolved and requires targeted evidence before promotion.",
                "falsifier": "Deterministic evidence establishes that the challenged condition prevents the security-relevant flow.",
                "prediction": "Resolving the critic's stated missing evidence will move the hypothesis toward rejection or stronger support.",
                "requested_evidence": requested,
                "assumptions": [
                    "Syntactic guard detection alone does not prove security semantics."
                ],
            }

        if verdict == "SUPPORTS":
            requested = list(packet.critic_missing_evidence) or [
                "Independent trust-boundary evidence for the candidate source."
            ]
            return {
                "schema_version": "1",
                "proposal_kind": "EVIDENCE_REQUEST",
                "disposition": "SEEK_EVIDENCE",
                "statement": "The hypothesis survives current falsification but is not yet proven exploitable.",
                "falsifier": packet.hypothesis_falsifier,
                "prediction": packet.hypothesis_prediction,
                "requested_evidence": requested,
                "assumptions": [
                    "Function-parameter origin alone does not prove attacker control."
                ],
            }

        return {
            "schema_version": "1",
            "proposal_kind": "EVIDENCE_REQUEST",
            "disposition": "SEEK_EVIDENCE",
            "statement": "The available evidence is insufficient for a stable research conclusion.",
            "falsifier": packet.hypothesis_falsifier,
            "prediction": packet.hypothesis_prediction,
            "requested_evidence": list(packet.critic_missing_evidence),
            "assumptions": [],
        }
