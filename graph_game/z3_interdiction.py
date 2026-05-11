from __future__ import annotations

import random

from z3 import And, BoolVector, If, Implies, Int, Not, Optimize, Or, PbEq, Sum, sat, simplify


def get_safety_status(scenario, attack, defend):
    radius = scenario.attack_radius
    vertices = scenario.g.V
    neighbors = scenario.g.neighbors
    safe = [Or(defend[i], Not(attack[i])) for i in range(vertices)]
    for _ in range(radius):
        updated = []
        for i in range(vertices):
            safe_conditions = [defend[i]]
            if neighbors[i]:
                safe_conditions.append(And([safe[neighbor] for neighbor in neighbors[i]]))
            updated.append(simplify(And(Not(attack[i]), Or(safe_conditions))))
        safe = updated
    return safe


def get_attack_delta(scenario, attack, defend, safe, remove_attack=None, add_attack=None):
    cover = scenario.g.get_cover(scenario.attack_radius)
    vertices = scenario.g.V
    if remove_attack is not None:
        new_attack = [False if i == remove_attack else attack[i] for i in range(vertices)]
        influenced = cover[remove_attack]
    elif add_attack is not None:
        new_attack = [True if i == add_attack else attack[i] for i in range(vertices)]
        influenced = cover[add_attack]
    else:
        raise ValueError("Either remove_attack or add_attack must be provided.")
    new_safe = get_safety_status(scenario, new_attack, defend)
    return simplify(
        Sum([If(new_safe[i] == safe[i], 0, If(new_safe[i], -1, 1)) for i in influenced])
    )


def solve_defense_problem(scenario):
    vertices = scenario.g.V
    attack = BoolVector("attack", vertices)
    defend = BoolVector("defend", vertices)
    safe = BoolVector("safe", vertices)
    computed_safe = get_safety_status(scenario, attack, defend)
    attack_inc = []
    attack_dec = []

    solver = Optimize()
    solver.set("timeout", 30 * 60 * 1000)
    for i in range(vertices):
        solver.add(safe[i] == computed_safe[i])
        inc = Int(f"attack_inc_{i}")
        dec = Int(f"attack_dec_{i}")
        solver.add(inc == get_attack_delta(scenario, attack, defend, safe, add_attack=i))
        solver.add(dec == get_attack_delta(scenario, attack, defend, safe, remove_attack=i))
        attack_inc.append(inc)
        attack_dec.append(dec)

    solver.add(PbEq([(defend[i], 1) for i in range(vertices)], scenario.budget_D))
    solver.add(PbEq([(attack[i], 1) for i in range(vertices)], scenario.budget_A))
    for i in range(vertices):
        solver.add(Implies(defend[i], Not(attack[i])))
        solver.add_soft(safe[i], 1)

    for remove_attack in range(vertices):
        for add_attack in range(vertices):
            if remove_attack == add_attack:
                continue
            valid_attack = And(attack[remove_attack], Not(attack[add_attack]), Not(defend[add_attack]))
            solver.add(Implies(valid_attack, attack_inc[add_attack] + attack_dec[remove_attack] <= 0))

    if solver.check() != sat:
        return None, None, None
    model = solver.model()
    defended_nodes = [i for i in range(vertices) if model.evaluate(defend[i], model_completion=True)]
    attacked_nodes = [i for i in range(vertices) if model.evaluate(attack[i], model_completion=True)]
    safe_nodes = [i for i in range(vertices) if model.evaluate(safe[i], model_completion=True)]
    return defended_nodes, attacked_nodes, safe_nodes


class Solver:
    def solve_with_defense(self, scenario, defense_choices):
        defense_choices = set(defense_choices)
        open_nodes = list(set(range(scenario.g.V)) - defense_choices)
        if len(open_nodes) < scenario.budget_A:
            raise ValueError("Not enough open nodes to attack.")
        random.shuffle(open_nodes)
        attack_choices = set(open_nodes[: scenario.budget_A])
        current_value = scenario.evaluate(attack_choices, defense_choices)
        while True:
            flip_from = None
            flip_to = None
            for attacked_node in attack_choices:
                for candidate in open_nodes:
                    if candidate in attack_choices or candidate in defense_choices:
                        continue
                    if scenario.evaluate((attack_choices - {attacked_node}) | {candidate}, defense_choices) < current_value:
                        flip_from = attacked_node
                        flip_to = candidate
                        break
                if flip_from is not None:
                    break
            if flip_from is None:
                break
            attack_choices = (attack_choices - {flip_from}) | {flip_to}
            current_value = scenario.evaluate(attack_choices, defense_choices)
        return attack_choices, current_value

    def get_defense(self, scenario):
        defended, _, _ = solve_defense_problem(scenario)
        if defended is None:
            raise TimeoutError("Z3 timed out.")
        return defended

    def solve(self, scenario):
        defense_choices = self.get_defense(scenario)
        min_safe = 999999
        best_attack = None
        for _ in range(100):
            attack_choices, safe_count = self.solve_with_defense(scenario, defense_choices)
            if safe_count < min_safe:
                min_safe = safe_count
                best_attack = attack_choices
        return best_attack, defense_choices, min_safe
