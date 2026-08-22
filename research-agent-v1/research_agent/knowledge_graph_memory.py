from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class GraphNode:

    id: str

    kind: str

    data: dict = field(
        default_factory=dict
    )



@dataclass
class GraphEdge:

    source: str

    relation: str

    target: str



class KnowledgeGraphMemory:


    def __init__(self):

        self.nodes = {}

        self.edges = []



    def add_node(
        self,
        kind: str,
        data: dict,
        node_id=None,
    ):

        node = GraphNode(
            id=node_id or
            f"NODE-{uuid4().hex[:12]}",

            kind=kind,

            data=data,
        )


        self.nodes[node.id] = node


        return node



    def connect(
        self,
        source: str,
        relation: str,
        target: str,
    ):

        edge = GraphEdge(
            source=source,
            relation=relation,
            target=target,
        )


        self.edges.append(
            edge
        )


        return edge



    def neighbors(
        self,
        node_id: str,
    ):

        result = []


        for edge in self.edges:

            if edge.source == node_id:

                result.append(
                    {
                        "relation":
                            edge.relation,

                        "target":
                            edge.target,
                    }
                )


        return result



    def lineage(
        self,
        node_id: str,
    ):

        visited = set()

        result = []


        def walk(current):

            for edge in self.edges:

                if edge.source == current:

                    if edge.target not in visited:

                        visited.add(
                            edge.target
                        )

                        result.append(
                            edge.target
                        )

                        walk(
                            edge.target
                        )


        walk(node_id)


        return result
