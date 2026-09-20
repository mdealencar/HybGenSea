import numpy as np

from hybgensea import solve_cvrp

# Fixed random instance, large enough that a one-iteration run does not reach the
# reference solution on its own. That gap is what makes the round trip meaningful:
# a seed that never reached the search would leave the warm start no better than
# the cold one, rather than merely failing to improve on the reference.
N = 60
CAPACITY = 60.0


def get_instance():
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 1000, N)
    y = rng.uniform(0, 1000, N)
    demands = np.concatenate([[0.0], rng.integers(1, 20, N - 1).astype(float)])
    return x, y, demands


def solve(x, y, demands, **kwargs):
    # nbIter with the default timeLimit of 0 keeps the runs deterministic and
    # independent of machine speed.
    return solve_cvrp(x, y, demands, CAPACITY, seed=1, verbose=False, **kwargs)


def test_round_trip_best_solution():
    x, y, demands = get_instance()
    reference = solve(x, y, demands, nbIter=2000)
    cold = solve(x, y, demands, nbIter=1)

    # RoutingSolution.routes is an initial_solutions entry with no conversion.
    warm = solve(x, y, demands, nbIter=1, initial_solutions=[reference.routes])

    assert warm.cost <= reference.cost
    assert warm.cost < cold.cost


def test_round_trip_feasible_population():
    x, y, demands = get_instance()
    reference = solve(x, y, demands, nbIter=2000)
    cold = solve(x, y, demands, nbIter=1)

    seeds = [individual.routes for individual in reference.feasible_population]
    assert len(seeds) == reference.n_feasible > 0

    # Every member of the feasible subpopulation is feasible by construction, so
    # the whole population re-seeds without initial_solutions_allow_infeasible.
    warm = solve(x, y, demands, nbIter=1, initial_solutions=seeds)

    assert warm.cost <= reference.cost
    assert warm.cost < cold.cost
