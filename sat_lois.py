from __future__ import annotations

import argparse
from fractions import Fraction

from itertools import combinations

from z3 import And, Bool, Exists, If, Not, RealVal, Solver, Sum, sat

from cng import build_synthetic_cng


def real(value: float) -> Fraction:
    return Fraction(str(value))


def real_val(value: float) -> object:
    fraction = real(value)
    return RealVal(f"{fraction.numerator}/{fraction.denominator}")


def payoff_terms(cng, defend, attack):
    defender_terms = []
    attacker_terms = []
    for i in range(cng.size):
        defender_terms.append(
            If(
                And(defend[i], attack[i]),
                real_val(cng.eta * cng.payoff_d[i]),
                If(
                    And(defend[i], Not(attack[i])),
                    real_val(cng.epsilon * cng.payoff_d[i]),
                    If(
                        And(Not(defend[i]), attack[i]),
                        real_val(cng.delta * cng.payoff_d[i]),
                        real_val(cng.payoff_d[i]),
                    ),
                ),
            )
        )
        attacker_terms.append(
            If(
                And(defend[i], attack[i]),
                real_val((1 - cng.eta) * cng.payoff_a[i]),
                If(
                    And(defend[i], Not(attack[i])),
                    real_val(0),
                    If(
                        And(Not(defend[i]), attack[i]),
                        real_val(cng.payoff_a[i]),
                        real_val(-cng.gamma * cng.payoff_a[i]),
                    ),
                ),
            )
        )
    return Sum(defender_terms), Sum(attacker_terms)


def weighted_sum(bits, weights):
    return Sum([If(bits[i], weights[i], 0) for i in range(len(bits))])


def hamming_distance(lhs, rhs):
    return Sum([If(lhs[i] != rhs[i], 1, 0) for i in range(len(lhs))])


def no_better_deviation(solver, base_bits, alt_bits, max_flips, budget_limit, weights, base_payoff, alt_payoff):
    solver.add(
        Not(
            Exists(
                alt_bits,
                And(
                    hamming_distance(base_bits, alt_bits) >= 1,
                    hamming_distance(base_bits, alt_bits) <= max_flips,
                    weighted_sum(alt_bits, weights) <= real_val(budget_limit),
                    alt_payoff > base_payoff,
                ),
            )
        )
    )


def evaluate_payoffs(cng, defend_values: list[int], attack_values: list[int]) -> tuple[float, float]:
    payoff_d = 0.0
    payoff_a = 0.0
    for i in range(cng.size):
        payoff_d += cng.payoff_d[i] * (
            (defend_values[i] * attack_values[i] * cng.eta)
            + (defend_values[i] * (1 - attack_values[i]) * cng.epsilon)
            + ((1 - defend_values[i]) * attack_values[i] * cng.delta)
            + ((1 - defend_values[i]) * (1 - attack_values[i]))
        )
        payoff_a += cng.payoff_a[i] * (
            (defend_values[i] * attack_values[i] * (1 - cng.eta))
            + ((1 - defend_values[i]) * attack_values[i])
            - ((1 - defend_values[i]) * (1 - attack_values[i]) * cng.gamma)
        )
    return payoff_d, payoff_a


def cost_within_budget(bits: list[int], weights: list[int], budget: float) -> bool:
    return sum(bit * weight for bit, weight in zip(bits, weights)) <= budget + 1e-9


def has_profitable_deviation(
    current_bits: list[int],
    other_bits: list[int],
    locality: int,
    weights: list[int],
    budget: float,
    payoff_fn,
) -> bool:
    active = [i for i, bit in enumerate(current_bits) if bit == 1]
    inactive = [i for i, bit in enumerate(current_bits) if bit == 0]
    baseline = payoff_fn(current_bits)
    max_flips = min(locality, len(current_bits))
    for flips in range(1, max_flips + 1):
        for down_count in range(flips + 1):
            up_count = flips - down_count
            if down_count > len(active) or up_count > len(inactive):
                continue
            for downs in combinations(active, down_count):
                for ups in combinations(inactive, up_count):
                    candidate = current_bits[:]
                    for idx in downs:
                        candidate[idx] = 0
                    for idx in ups:
                        candidate[idx] = 1
                    if not cost_within_budget(candidate, weights, budget):
                        continue
                    if payoff_fn(candidate) > baseline + 1e-9:
                        return True
    return False


def verify_local_optimum(cng, defend_values: list[int], attack_values: list[int], locality: int) -> bool:
    def defender_payoff(defend_bits: list[int]) -> float:
        return evaluate_payoffs(cng, defend_bits, attack_values)[0]

    def attacker_payoff(attack_bits: list[int]) -> float:
        return evaluate_payoffs(cng, defend_values, attack_bits)[1]

    return not has_profitable_deviation(
        defend_values, attack_values, locality, cng.cost_d, cng.budget_d, defender_payoff
    ) and not has_profitable_deviation(
        attack_values, defend_values, locality, cng.cost_a, cng.budget_a, attacker_payoff
    )


def solve_sat_lois(size: int, seed: int, locality: int = 2) -> dict[str, object]:
    cng = build_synthetic_cng(size, seed)
    cng.initialize()
    solver = Solver()

    defend = [Bool(f"defend_{i}") for i in range(cng.size)]
    attack = [Bool(f"attack_{i}") for i in range(cng.size)]
    defend_alt = [Bool(f"defend_alt_{i}") for i in range(cng.size)]
    attack_alt = [Bool(f"attack_alt_{i}") for i in range(cng.size)]

    payoff_d, payoff_a = payoff_terms(cng, defend, attack)
    alt_payoff_d, _ = payoff_terms(cng, defend_alt, attack)
    _, alt_payoff_a = payoff_terms(cng, defend, attack_alt)

    solver.add(weighted_sum(defend, cng.cost_d) <= real_val(cng.budget_d))
    solver.add(weighted_sum(attack, cng.cost_a) <= real_val(cng.budget_a))

    no_better_deviation(solver, defend, defend_alt, locality, cng.budget_d, cng.cost_d, payoff_d, alt_payoff_d)
    no_better_deviation(solver, attack, attack_alt, locality, cng.budget_a, cng.cost_a, payoff_a, alt_payoff_a)

    if solver.check() != sat:
        raise RuntimeError("No SAT-LOIS solution found for the given instance.")
    model = solver.model()
    defend_values = [1 if model.evaluate(defend[i], model_completion=True) else 0 for i in range(cng.size)]
    attack_values = [1 if model.evaluate(attack[i], model_completion=True) else 0 for i in range(cng.size)]
    payoff_d_value, payoff_a_value = evaluate_payoffs(cng, defend_values, attack_values)
    return {
        "defend": defend_values,
        "attack": attack_values,
        "f_d": payoff_d_value,
        "f_a": payoff_a_value,
        "PoS": cng.max_payoff_d / payoff_d_value,
        "PoA": None if payoff_a_value <= 0 else cng.max_payoff_a / payoff_a_value,
        "locality": locality,
        "verified": verify_local_optimum(cng, defend_values, attack_values, locality) if size <= 20 else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Find a SAT-LOIS solution for the critical node game.")
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--locality", type=int, default=2)
    args = parser.parse_args()

    result = solve_sat_lois(args.size, args.seed, args.locality)
    for key in ("f_d", "f_a", "PoS", "PoA", "locality", "verified"):
        value = result[key]
        if value is None:
            value = "n/a"
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
