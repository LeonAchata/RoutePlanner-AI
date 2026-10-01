"""Visiting-order optimisation (a travelling salesman variant).

The route always starts at node 0 (the origin). It either ends anywhere
(open path) or comes back to node 0 (round trip). Driving distances are not
symmetric, so every cost here is computed on the directed matrix.

Strategy by size:
- up to EXACT_LIMIT nodes: Held-Karp dynamic programming, guaranteed optimal
- larger: OR-Tools with guided local search, falling back to
  nearest neighbour + 2-opt if OR-Tools is unavailable or finds nothing
"""
import itertools
import logging
from typing import Sequence

logger = logging.getLogger(__name__)

Matrix = Sequence[Sequence[float]]

EXACT_LIMIT = 12
ORTOOLS_TIME_LIMIT_SECONDS = 2


def route_cost(matrix: Matrix, route: Sequence[int]) -> float:
    return sum(matrix[a][b] for a, b in zip(route, route[1:]))


def solve(matrix: Matrix, return_to_start: bool = False) -> tuple[list[int], float]:
    """Return (visiting order, total cost). The order starts with 0 and ends
    with 0 again when `return_to_start` is set."""
    n = len(matrix)
    if n == 0:
        return [], 0.0
    if n == 1:
        return [0], 0.0

    if n <= EXACT_LIMIT:
        route = _held_karp(matrix, return_to_start)
    else:
        route = _ortools(matrix, return_to_start) or _two_opt(
            matrix, _nearest_neighbour(matrix, return_to_start), return_to_start
        )
    return route, route_cost(matrix, route)


def _held_karp(matrix: Matrix, return_to_start: bool) -> list[int]:
    n = len(matrix)
    # dp[(mask, j)] = (cost, previous node) for paths 0 -> ... -> j visiting
    # exactly the nodes in `mask` (bit k-1 represents node k).
    dp: dict[tuple[int, int], tuple[float, int]] = {}
    for j in range(1, n):
        dp[(1 << (j - 1), j)] = (matrix[0][j], 0)

    for size in range(2, n):
        for subset in itertools.combinations(range(1, n), size):
            mask = 0
            for node in subset:
                mask |= 1 << (node - 1)
            for j in subset:
                prev_mask = mask & ~(1 << (j - 1))
                best = min(
                    (dp[(prev_mask, k)][0] + matrix[k][j], k)
                    for k in subset
                    if k != j
                )
                dp[(mask, j)] = best

    full = (1 << (n - 1)) - 1
    tail = (lambda j: matrix[j][0]) if return_to_start else (lambda j: 0.0)
    _, last = min((dp[(full, j)][0] + tail(j), j) for j in range(1, n))

    route = []
    mask, node = full, last
    while node != 0:
        route.append(node)
        _, prev = dp[(mask, node)]
        mask &= ~(1 << (node - 1))
        node = prev
    route.append(0)
    route.reverse()
    if return_to_start:
        route.append(0)
    return route


def _nearest_neighbour(matrix: Matrix, return_to_start: bool) -> list[int]:
    unvisited = set(range(1, len(matrix)))
    route = [0]
    while unvisited:
        here = route[-1]
        nearest = min(unvisited, key=lambda k: matrix[here][k])
        route.append(nearest)
        unvisited.remove(nearest)
    if return_to_start:
        route.append(0)
    return route


def _two_opt(matrix: Matrix, route: list[int], return_to_start: bool, max_passes: int = 100) -> list[int]:
    """Reverse segments while it helps. Node 0 at the start (and at the end of
    a round trip) never moves."""
    best = list(route)
    best_cost = route_cost(matrix, best)
    last_movable = len(best) - (2 if return_to_start else 1)

    for _ in range(max_passes):
        improved = False
        for i in range(1, last_movable):
            for j in range(i + 1, last_movable + 1):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                cost = route_cost(matrix, candidate)
                if cost < best_cost - 1e-9:
                    best, best_cost, improved = candidate, cost, True
        if not improved:
            break
    return best


def _ortools(matrix: Matrix, return_to_start: bool) -> list[int] | None:
    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    except ImportError:
        logger.warning("OR-Tools not installed, using the 2-opt heuristic")
        return None

    n = len(matrix)
    # For an open path add a dummy end node that every node reaches for free;
    # the solver then picks the best place to stop.
    size = n if return_to_start else n + 1
    end = 0 if return_to_start else n
    manager = pywrapcp.RoutingIndexManager(size, 1, [0], [end])
    routing = pywrapcp.RoutingModel(manager)

    def cost(from_index: int, to_index: int) -> int:
        a, b = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        if a >= n or b >= n:
            return 0
        return int(round(matrix[a][b] * 1000))

    callback = routing.RegisterTransitCallback(cost)
    routing.SetArcCostEvaluatorOfAllVehicles(callback)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = ORTOOLS_TIME_LIMIT_SECONDS

    solution = routing.SolveWithParameters(params)
    if solution is None:
        return None

    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    if return_to_start:
        route.append(0)
    return route
