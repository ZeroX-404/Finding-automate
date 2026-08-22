from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()



@dataclass
class ApprovalRequest:

    id: str = field(
        default_factory=lambda:
        f"APR-{uuid4().hex[:12]}"
    )

    agent: str = ""

    action: str = ""

    status: str = "PENDING"

    reviewer: str | None = None

    reason: str | None = None

    created_at: str = field(
        default_factory=utc_now
    )



class HumanOversightGateway:


    def __init__(self):

        self.requests = []



    def request(
        self,
        agent: str,
        action: str,
    ):

        approval = ApprovalRequest(
            agent=agent,
            action=action,
        )

        self.requests.append(
            approval
        )

        return approval



    def approve(
        self,
        request_id: str,
        reviewer: str,
        reason: str,
    ):

        request = self._find(
            request_id
        )

        request.status = "APPROVED"

        request.reviewer = reviewer

        request.reason = reason

        return request



    def reject(
        self,
        request_id: str,
        reviewer: str,
        reason: str,
    ):

        request = self._find(
            request_id
        )

        request.status = "REJECTED"

        request.reviewer = reviewer

        request.reason = reason

        return request



    def _find(
        self,
        request_id: str,
    ):

        for request in self.requests:

            if request.id == request_id:

                return request


        raise ValueError(
            "Approval request not found"
        )
