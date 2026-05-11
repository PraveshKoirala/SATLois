from __future__ import annotations

import argparse
import random

from graph import Line, MST, Ring, Sparse30
from heuristics import (
    BetweennessCentrality,
    ClosenessCentrality,
    DegreeCentrality,
    EigenCentrality,
    ShapleyCentrality,
)
from scenario import Scenario
from z3_interdiction import Solver


def run_benchmark(vertices: int, budget_d: int, budget_a: int, radius: int, samples: int, seed: int) -> None:
    random.seed(seed)
    graph_families = [MST, Line, Sparse30, Ring]
    heuristics = [
        ("Eigenvalue", EigenCentrality()),
        ("Closeness", ClosenessCentrality()),
        ("Shapley", ShapleyCentrality()),
        ("Degree", DegreeCentrality()),
        ("Betweenness", BetweennessCentrality()),
    ]
    timed_out = 0

    for graph_class in graph_families:
        for _ in range(samples):
            graph = graph_class(vertices)
            scenario = Scenario(graph, budget_d, budget_a, radius)
            try:
                _, _, z3_safe = Solver().solve(scenario)
                print(f"Z3, {z3_safe}, {graph}")
            except TimeoutError:
                timed_out += 1
                continue
            for label, heuristic in heuristics:
                _, _, heuristic_safe = heuristic.solve(scenario)
                print(f"{label}, {heuristic_safe}, {graph}")
    print(f"Timed out: {timed_out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the graph interdiction benchmark used by the SAT-LOIS paper.")
    parser.add_argument("--vertices", type=int, default=50)
    parser.add_argument("--budget-d", type=int, default=5)
    parser.add_argument("--budget-a", type=int, default=2)
    parser.add_argument("--radius", type=int, default=5)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=75)
    args = parser.parse_args()
    run_benchmark(args.vertices, args.budget_d, args.budget_a, args.radius, args.samples, args.seed)


if __name__ == "__main__":
    main()
