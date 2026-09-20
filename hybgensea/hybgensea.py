from collections.abc import Sequence
from dataclasses import dataclass
import numpy as np
import sys

from . import _core


C_DBL_MAX = sys.float_info.max

DEFAULT_ALGO_PARAMS = _core.default_algorithm_parameters()


def _ap_c_args(**overrides):
    resolved = {**DEFAULT_ALGO_PARAMS, **overrides}
    return (
        int(resolved['nbGranular']),
        int(resolved['mu']),
        int(resolved['lambda_']),
        int(resolved['nbElite']),
        int(resolved['nbClose']),
        int(resolved['nbIterPenaltyManagement']),
        float(resolved['targetFeasible']),
        float(resolved['penaltyDecrease']),
        float(resolved['penaltyIncrease']),
        int(resolved['seed']),
        int(resolved['nbIter']),
        int(resolved['nbIterTraces']),
        float(resolved['timeLimit']),
        bool(resolved['useSwapStar']),
    )


def _coerce_initial_solutions(initial_solutions):
    """Normalise initial_solutions to list[list[list[int]]] before crossing into C++.

    Doing it here means a malformed entry raises a TypeError/ValueError naming the
    offending element, rather than a generic nanobind overload-resolution error.
    """
    if initial_solutions is None:
        return []
    return [[[int(client) for client in route] for route in solution]
            for solution in initial_solutions]


def solve_cvrp_dist_mtx(
    dist_mtx,
    demands,
    vehicle_capacity,
    *,
    x_coords=None,
    y_coords=None,
    service_times=None,
    duration_limit=None,
    num_vehicles=-1,
    initial_solutions=None,
    initial_solutions_allow_infeasible=False,
    extract_all_feasible=True,
    verbose=True,
    log_callback=None,
    **ap_kwargs,
):
    """Solve CVRP with a pre-computed distance matrix.

    Args:
        dist_mtx: (n, n) distance matrix (float64, C-contiguous)
        demands: (n,) demand per node, depot demand must be 0
        vehicle_capacity: maximum vehicle capacity
        x_coords: (n,) x coordinates (optional, for SWAP*)
        y_coords: (n,) y coordinates (optional, for SWAP*)
        service_times: (n,) service duration per node (default: zeros)
        duration_limit: route duration limit (default: unconstrained)
        num_vehicles: maximum number of vehicles (default: unlimited)
        initial_solutions: solutions used to seed the search, as a list of
            solutions, each a list of routes, each a list of 1-based client
            indices (the depot is implicit). This is exactly the shape of
            RoutingSolution.routes with one more level of nesting, so
            initial_solutions=[result.routes] re-seeds a previous result.
            Every client must be visited exactly once per solution and the
            number of routes must not exceed the fleet size.
        initial_solutions_allow_infeasible: accept seeds that breach the
            capacity or duration limits (rejected by default)
        extract_all_feasible: keep the whole final feasible subpopulation, not
            just the best solution. Members are boxed into Python lazily, so
            this costs a bounded copy and nothing more until they are read.
        verbose: print solver log
        log_callback: callable receiving each log line
        **ap_kwargs: algorithm parameters (seed, timeLimit, nbGranular, etc.)

    Returns:
        RoutingSolution with .cost, .time, .routes, .n_routes, .log,
        .n_feasible and .feasible_population (None if extract_all_feasible
        is False).
    """
    dist_mtx = np.ascontiguousarray(dist_mtx, dtype=np.float64)
    demands = np.ascontiguousarray(demands, dtype=np.float64)
    n = len(demands)

    if x_coords is None or y_coords is None:
        x_coords = np.zeros(n, dtype=np.float64)
        y_coords = np.zeros(n, dtype=np.float64)
    else:
        x_coords = np.ascontiguousarray(x_coords, dtype=np.float64)
        y_coords = np.ascontiguousarray(y_coords, dtype=np.float64)

    if service_times is None:
        service_times = np.zeros(n, dtype=np.float64)
    else:
        service_times = np.ascontiguousarray(service_times, dtype=np.float64)

    if duration_limit is None:
        is_duration_constraint = False
        duration_limit = float(C_DBL_MAX)
    else:
        is_duration_constraint = True
        duration_limit = float(duration_limit)

    sol = _core.solve_cvrp_dist_mtx(
        x_coords, y_coords, dist_mtx, service_times, demands,
        float(vehicle_capacity), duration_limit, bool(is_duration_constraint),
        int(num_vehicles),
        *_ap_c_args(**ap_kwargs),
        bool(verbose), log_callback,
        _coerce_initial_solutions(initial_solutions),
        bool(initial_solutions_allow_infeasible), bool(extract_all_feasible),
    )
    return RoutingSolution(sol)


def solve_cvrp(
    x_coords,
    y_coords,
    demands,
    vehicle_capacity,
    *,
    service_times=None,
    duration_limit=None,
    num_vehicles=-1,
    initial_solutions=None,
    initial_solutions_allow_infeasible=False,
    extract_all_feasible=True,
    rounding=True,
    verbose=True,
    log_callback=None,
    **ap_kwargs,
):
    """Solve CVRP from coordinates (distance matrix computed internally).

    Args:
        x_coords: (n,) x coordinates
        y_coords: (n,) y coordinates
        demands: (n,) demand per node, depot demand must be 0
        vehicle_capacity: maximum vehicle capacity
        service_times: (n,) service duration per node (default: zeros)
        duration_limit: route duration limit (default: unconstrained)
        num_vehicles: maximum number of vehicles (default: unlimited)
        initial_solutions: solutions used to seed the search, as a list of
            solutions, each a list of routes, each a list of 1-based client
            indices (the depot is implicit). This is exactly the shape of
            RoutingSolution.routes with one more level of nesting, so
            initial_solutions=[result.routes] re-seeds a previous result.
            Every client must be visited exactly once per solution and the
            number of routes must not exceed the fleet size.
        initial_solutions_allow_infeasible: accept seeds that breach the
            capacity or duration limits (rejected by default)
        extract_all_feasible: keep the whole final feasible subpopulation, not
            just the best solution. Members are boxed into Python lazily, so
            this costs a bounded copy and nothing more until they are read.
        rounding: round Euclidean distances to integers
        verbose: print solver log
        log_callback: callable receiving each log line
        **ap_kwargs: algorithm parameters (seed, timeLimit, nbGranular, etc.)

    Returns:
        RoutingSolution with .cost, .time, .routes, .n_routes, .log,
        .n_feasible and .feasible_population (None if extract_all_feasible
        is False).
    """
    x_coords = np.ascontiguousarray(x_coords, dtype=np.float64)
    y_coords = np.ascontiguousarray(y_coords, dtype=np.float64)
    demands = np.ascontiguousarray(demands, dtype=np.float64)
    n = len(demands)

    if service_times is None:
        service_times = np.zeros(n, dtype=np.float64)
    else:
        service_times = np.ascontiguousarray(service_times, dtype=np.float64)

    if duration_limit is None:
        is_duration_constraint = False
        duration_limit = float(C_DBL_MAX)
    else:
        is_duration_constraint = True
        duration_limit = float(duration_limit)

    sol = _core.solve_cvrp(
        x_coords, y_coords, service_times, demands,
        float(vehicle_capacity), duration_limit, bool(rounding),
        bool(is_duration_constraint), int(num_vehicles),
        *_ap_c_args(**ap_kwargs),
        bool(verbose), log_callback,
        _coerce_initial_solutions(initial_solutions),
        bool(initial_solutions_allow_infeasible), bool(extract_all_feasible),
    )
    return RoutingSolution(sol)


def solve_tsp(
    x_coords=None,
    y_coords=None,
    dist_mtx=None,
    *,
    initial_solutions=None,
    initial_solutions_allow_infeasible=False,
    extract_all_feasible=True,
    rounding=True,
    verbose=True,
    log_callback=None,
    **ap_kwargs,
):
    """Solve TSP (single-vehicle, unit demands).

    Provide either (x_coords, y_coords) or dist_mtx.
    """
    if dist_mtx is not None:
        dist_mtx = np.asarray(dist_mtx, dtype=np.float64)
        n = dist_mtx.shape[0]
        demands = np.ones(n, dtype=np.float64)
        demands[0] = 0.0
        return solve_cvrp_dist_mtx(
            dist_mtx, demands, float(n),
            x_coords=x_coords, y_coords=y_coords,
            num_vehicles=1,
            initial_solutions=initial_solutions,
            initial_solutions_allow_infeasible=initial_solutions_allow_infeasible,
            extract_all_feasible=extract_all_feasible,
            verbose=verbose, log_callback=log_callback,
            **ap_kwargs,
        )
    else:
        x_coords = np.asarray(x_coords, dtype=np.float64)
        y_coords = np.asarray(y_coords, dtype=np.float64)
        n = len(x_coords)
        demands = np.ones(n, dtype=np.float64)
        demands[0] = 0.0
        return solve_cvrp(
            x_coords, y_coords, demands, float(n),
            rounding=rounding, num_vehicles=1,
            initial_solutions=initial_solutions,
            initial_solutions_allow_infeasible=initial_solutions_allow_infeasible,
            extract_all_feasible=extract_all_feasible,
            verbose=verbose, log_callback=log_callback,
            **ap_kwargs,
        )


class Individual:
    """A member of the final feasible subpopulation.

    An immutable copy, detached from the solver's population: unlike upstream's
    Individual it cannot be mutated or re-evaluated. Because every member of that
    subpopulation is feasible, cost is the plain route distance, with no penalty
    term, and so is comparable across runs.

    Routes are converted to Python on first access and cached, so reading only
    cost or n_routes never pays for them.
    """

    __slots__ = ("_member", "_routes", "cost", "n_routes")

    def __init__(self, member):
        self.cost = member.cost
        self.n_routes = member.n_routes
        self._member = member
        self._routes = None

    @property
    def routes(self):
        """Routes as lists of 1-based client indices, valid as an initial_solutions entry."""
        if self._routes is None:
            self._routes = self._member.routes
        return self._routes

    def __repr__(self):
        return f"Individual(cost={self.cost}, n_routes={self.n_routes})"


class _SubPopulation(Sequence):
    """Lazy view of a subpopulation, ordered best first.

    Indexing materialises one Individual, so [:k] costs k and len() costs nothing.
    """

    __slots__ = ("_cache", "_get", "_n")

    def __init__(self, n, get):
        self._n = n
        self._get = get
        self._cache = {}

    def __len__(self):
        return self._n

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(self._n))]
        if index < 0:
            index += self._n
        if not 0 <= index < self._n:
            raise IndexError(index)
        individual = self._cache.get(index)
        if individual is None:
            individual = self._cache[index] = Individual(self._get(index))
        return individual

    def __repr__(self):
        return f"<_SubPopulation of {self._n}>"


class RoutingSolution:
    def __init__(self, sol):
        self.cost = sol.cost
        self.time = sol.time
        self.routes = sol.routes
        self.n_routes = len(self.routes)
        self.log = sol.log
        self.n_feasible = sol.n_feasible
        self.feasible_population = (
            _SubPopulation(sol.n_feasible, sol.feasible_member)
            if sol.extracted_all_feasible else None
        )


# --- Legacy API (kept for backward compatibility with tests/other users) ---

_d = DEFAULT_ALGO_PARAMS

@dataclass
class AlgorithmParameters:
    nbGranular: int = _d['nbGranular']
    mu: int = _d['mu']
    lambda_: int = _d['lambda_']
    nbElite: int = _d['nbElite']
    nbClose: int = _d['nbClose']
    nbIterPenaltyManagement: int = _d['nbIterPenaltyManagement']
    targetFeasible: float = _d['targetFeasible']
    penaltyDecrease: float = _d['penaltyDecrease']
    penaltyIncrease: float = _d['penaltyIncrease']
    seed: int = _d['seed']
    nbIter: int = _d['nbIter']
    nbIterTraces: int = _d['nbIterTraces']
    timeLimit: float = _d['timeLimit']
    useSwapStar: bool = _d['useSwapStar']

del _d


class Solver:
    def __init__(self, parameters=AlgorithmParameters(), verbose=True, log_callback=None):
        self.algorithm_parameters = parameters
        self.verbose = bool(verbose)
        self.log_callback = log_callback

    def _ap_kwargs(self):
        ap = self.algorithm_parameters
        return dict(
            nbGranular=ap.nbGranular, mu=ap.mu, lambda_=ap.lambda_,
            nbElite=ap.nbElite, nbClose=ap.nbClose,
            nbIterPenaltyManagement=ap.nbIterPenaltyManagement,
            targetFeasible=ap.targetFeasible, penaltyDecrease=ap.penaltyDecrease,
            penaltyIncrease=ap.penaltyIncrease, seed=ap.seed, nbIter=ap.nbIter,
            nbIterTraces=ap.nbIterTraces, timeLimit=ap.timeLimit,
            useSwapStar=ap.useSwapStar,
        )

    def solve_cvrp(self, data, rounding=True):
        demand = np.asarray(data["demands"], dtype=np.float64)
        vehicle_capacity = float(data["vehicle_capacity"])

        depot = data.get("depot", 0)
        if depot != 0:
            raise ValueError("In HGS, the depot location must be 0.")

        kwargs = dict(
            num_vehicles=data.get("num_vehicles", -1),
            service_times=data.get("service_times"),
            duration_limit=data.get("duration_limit"),
            initial_solutions=data.get("initial_solutions"),
            initial_solutions_allow_infeasible=data.get(
                "initial_solutions_allow_infeasible", False),
            extract_all_feasible=data.get("extract_all_feasible", True),
            verbose=self.verbose,
            log_callback=self.log_callback,
            **self._ap_kwargs(),
        )

        x_coords = data.get("x_coordinates")
        y_coords = data.get("y_coordinates")
        dist_mtx = data.get("distance_matrix")

        if dist_mtx is not None:
            return solve_cvrp_dist_mtx(
                dist_mtx, demand, vehicle_capacity,
                x_coords=x_coords, y_coords=y_coords, **kwargs,
            )
        else:
            return solve_cvrp(
                x_coords, y_coords, demand, vehicle_capacity,
                rounding=rounding, **kwargs,
            )

    def solve_tsp(self, data, rounding=True):
        x_coords = data.get("x_coordinates")
        dist_mtx = data.get("distance_matrix")
        if dist_mtx is None:
            n_nodes = x_coords.size
        else:
            dist_mtx = np.asarray(dist_mtx)
            n_nodes = dist_mtx.shape[0]

        data["num_vehicles"] = 1
        data["depot"] = 0
        data["demands"] = np.ones(n_nodes)
        data["vehicle_capacity"] = n_nodes

        return self.solve_cvrp(data, rounding=rounding)
