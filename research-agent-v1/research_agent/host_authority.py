from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class ActionRequest:

    id: str = field(
        default_factory=lambda:
        f"ACT-{uuid4().hex[:12]}"
    )

    action: str = ""

    target: str = ""

    reason: str = ""

    risk: str = "LOW"



@dataclass
class PermissionRule:

    action: str

    decision: str
    # ALLOW / DENY / ASK



class HostAuthorityEngine:


    def __init__(self):

        self.rules = {

            "READ_FILE":
                "ALLOW",

            "RUN_TEST":
                "ASK",

            "RUN_COMMAND":
                "ASK",

            "MODIFY_SOURCE":
                "ASK",

            "DELETE_FILE":
                "DENY",

            "GIT_PUSH":
                "ASK",

        }


        self.history = []



    def request(
        self,
        action: str,
        target: str,
        reason: str,
    ):

        decision = (
            self.rules
            .get(
                action,
                "ASK"
            )
        )


        request = ActionRequest(
            action=action,
            target=target,
            reason=reason,
        )


        self.history.append(
            {
                "request":
                    request,

                "decision":
                    decision,
            }
        )


        return {
            "request_id":
                request.id,

            "action":
                action,

            "decision":
                decision,

            "reason":
                reason,
        }



    def approve(
        self,
        action: str,
    ):

        self.rules[action] = "ALLOW"



    def deny(
        self,
        action: str,
    ):

        self.rules[action] = "DENY"
