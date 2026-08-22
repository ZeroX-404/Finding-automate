from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class AgentNode:

    name: str

    depends_on: list[str] = field(
        default_factory=list
    )

    result: dict | None = None



class MultiAgentExecutionGraph:


    def __init__(self):

        self.nodes: dict[str, AgentNode] = {}



    def add_agent(
        self,
        name: str,
        depends_on=None,
    ):

        self.nodes[name] = AgentNode(
            name=name,
            depends_on=depends_on or [],
        )



    def execution_order(self):

        visited = set()

        order = []


        def visit(name):

            if name in visited:
                return

            node = self.nodes[name]


            for dep in node.depends_on:

                visit(dep)


            visited.add(name)

            order.append(name)



        for name in self.nodes:

            visit(name)


        return order



    def run(
        self,
        executor,
    ):

        results = {}


        for agent in self.execution_order():

            results[agent] = executor(
                agent
            )


        return results
