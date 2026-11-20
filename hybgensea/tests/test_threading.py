"""Concurrent use from several threads.

The solver releases the GIL, so solves already overlap on regular CPython; on
free-threaded CPython the Python-side code runs in parallel as well.
"""

import sys
import sysconfig
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

from hybgensea import solve_cvrp

N = 40
CAPACITY = 60.0
SEEDS = range(1, 9)


def get_instance():
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 1000, N)
    y = rng.uniform(0, 1000, N)
    demands = np.concatenate([[0.0], rng.integers(1, 20, N - 1).astype(float)])
    return x, y, demands


def solve(seed):
    # nbIter with the default timeLimit of 0 keeps each run deterministic.
    x, y, demands = get_instance()
    lines = []
    result = solve_cvrp(x, y, demands, CAPACITY, seed=seed, nbIter=300,
                        verbose=True, log_callback=lines.append)
    return result, "".join(lines)


def test_gil_stays_disabled():
    if not sysconfig.get_config_var("Py_GIL_DISABLED"):
        pytest.skip("not a free-threaded build")
    # Importing an extension not marked free-threading safe re-enables the GIL.
    assert not sys._is_gil_enabled()


def test_concurrent_solves_match_sequential():
    sequential = [solve(seed) for seed in SEEDS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        concurrent = list(pool.map(solve, SEEDS))

    for (seq, _), (conc, conc_lines) in zip(sequential, concurrent, strict=True):
        assert conc.cost == seq.cost
        assert conc.routes == seq.routes
        # Each callback received exactly its own run's log, from its own thread.
        assert conc_lines == conc.log != ""


def test_concurrent_population_reads():
    result, _ = solve(1)
    population = result.feasible_population
    assert population is not None
    n = len(population)
    assert n > 0

    def read_all(_):
        return [population[i] for i in range(n)], [population[i].routes for i in range(n)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        reads = list(pool.map(read_all, range(8)))

    members, routes = reads[0]
    for other_members, other_routes in reads[1:]:
        # The lazy cache hands every thread the same Individual objects.
        assert all(a is b for a, b in zip(members, other_members, strict=True))
        assert other_routes == routes
