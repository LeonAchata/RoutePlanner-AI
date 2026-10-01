import itertools
import random

import pytest

from app.services import tsp_solver


def brute_force(matrix, return_to_start):
    n = len(matrix)
    best = None
    for perm in itertools.permutations(range(1, n)):
        route = [0, *perm] + ([0] if return_to_start else [])
        cost = tsp_solver.route_cost(matrix, route)
        if best is None or cost < best:
            best = cost
    return best


def random_matrix(n, seed, symmetric=False):
    rng = random.Random(seed)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                m[i][j] = m[j][i] if symmetric and j < i else rng.uniform(1, 50)
    return m


@pytest.mark.parametrize("n", [2, 3, 5, 7, 8])
@pytest.mark.parametrize("return_to_start", [False, True])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_exact_solver_matches_brute_force(n, return_to_start, seed):
    matrix = random_matrix(n, seed)
    route, cost = tsp_solver.solve(matrix, return_to_start)

    assert route[0] == 0
    assert sorted(set(route)) == list(range(n))
    assert len(route) == n + (1 if return_to_start else 0)
    if return_to_start:
        assert route[-1] == 0
    assert cost == pytest.approx(brute_force(matrix, return_to_start))
    assert cost == pytest.approx(tsp_solver.route_cost(matrix, route))


def test_single_location():
    assert tsp_solver.solve([[0.0]]) == ([0], 0.0)


def test_open_path_does_not_pay_for_return_leg():
    # Going 0 -> 1 -> 2 is cheap, but coming back from 2 is very expensive.
    matrix = [
        [0, 1, 10],
        [1, 0, 1],
        [100, 1, 0],
    ]
    route, cost = tsp_solver.solve(matrix, return_to_start=False)
    assert route == [0, 1, 2]
    assert cost == 2


@pytest.mark.parametrize("return_to_start", [False, True])
def test_large_instances_are_valid_and_reasonable(return_to_start):
    n = 18
    matrix = random_matrix(n, seed=42, symmetric=True)
    route, cost = tsp_solver.solve(matrix, return_to_start)

    assert route[0] == 0
    assert sorted(set(route)) == list(range(n))
    if return_to_start:
        assert route[-1] == 0
    nn = tsp_solver._nearest_neighbour(matrix, return_to_start)
    assert cost <= tsp_solver.route_cost(matrix, nn) + 1e-6


def test_two_opt_keeps_endpoints_fixed():
    matrix = random_matrix(9, seed=7)
    start = tsp_solver._nearest_neighbour(matrix, return_to_start=True)
    improved = tsp_solver._two_opt(matrix, start, return_to_start=True)
    assert improved[0] == 0 and improved[-1] == 0
    assert tsp_solver.route_cost(matrix, improved) <= tsp_solver.route_cost(matrix, start)
