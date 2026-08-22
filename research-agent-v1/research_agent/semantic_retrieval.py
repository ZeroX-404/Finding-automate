from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt



@dataclass
class ResearchCase:

    case_id: str

    features: set[str] = field(
        default_factory=set
    )

    outcome: str = ""



class SemanticResearchRetrieval:


    def __init__(self):

        self.cases = []



    def add_case(
        self,
        case_id: str,
        features: list[str],
        outcome: str,
    ):

        case = ResearchCase(
            case_id=case_id,
            features=set(features),
            outcome=outcome,
        )


        self.cases.append(
            case
        )


        return case



    def similarity(
        self,
        query_features,
        case_features,
    ):

        query = set(query_features)

        case = set(case_features)


        intersection = len(
            query & case
        )


        union = len(
            query | case
        )


        if union == 0:

            return 0.0


        return round(
            intersection / union,
            4,
        )



    def retrieve(
        self,
        features: list[str],
        limit: int = 3,
    ):

        ranked = []


        for case in self.cases:

            score = self.similarity(
                features,
                case.features,
            )


            ranked.append(
                {
                    "case_id":
                        case.case_id,

                    "score":
                        score,

                    "outcome":
                        case.outcome,
                }
            )


        return sorted(
            ranked,
            key=lambda x:
            x["score"],
            reverse=True,
        )[:limit]
