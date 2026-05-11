from __future__ import annotations


class Scenario:
    def __init__(self, graph, budget_d: int, budget_a: int, attack_radius: int):
        self.g = graph
        self.budget_D = budget_d
        self.budget_A = budget_a
        self.attack_radius = attack_radius

    def evaluate(self, attack_nodes: set[int], defense_nodes: set[int], return_list: bool = False):
        vertices = self.g.V
        attacked = [vertex in attack_nodes for vertex in range(vertices)]
        defended = [vertex in defense_nodes for vertex in range(vertices)]
        if attack_nodes & defense_nodes:
            raise ValueError("A node cannot be attacked and defended at the same time.")
        safe = [defended[i] or not attacked[i] for i in range(vertices)]
        for _ in range(self.attack_radius):
            new_safe = []
            for i in range(vertices):
                if defended[i]:
                    new_safe.append(True)
                elif attacked[i]:
                    new_safe.append(False)
                elif self.g.neighbors[i]:
                    new_safe.append(all(safe[neighbor] for neighbor in self.g.neighbors[i]))
                else:
                    new_safe.append(True)
            safe = new_safe
        if return_list:
            return safe, sum(safe)
        return sum(safe)
