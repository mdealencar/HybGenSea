# v0.2.0

[Commit history since v0.1.1](https://github.com/mdealencar/HybGenSea/compare/v0.1.1...v0.2.0)

## Important Changes

- The solvers accept `initial_solutions` to add to the first population. Each entry is a list of routes of 1-based client indices — `RoutingSolution.routes` with one more level of nesting — so a previous result can be handed straight back as `initial_solutions=[result.routes]`. Passed individuals do not draw from the random stream, so a warm started run stays comparable to a cold one at the same seed. `Solver.solve_cvrp` reads the same value from `data["initial_solutions"]`.
- Initial solutions that breach the capacity or duration limits are rejected unless `initial_solutions_allow_infeasible` is set. Routes per solution must together visit every client exactly once and must not outnumber the fleet size.
- `RoutingSolution` exposes the final feasible subpopulation as `.feasible_population`, ordered best first, so `[:k]` is the top k. Each `Individual` carries `routes`, `cost` and `n_routes`, and every member is valid as an `initial_solutions` entry with no filtering. `.n_feasible` is always reported.
- Population members are boxed into Python only on access: reading a member costs two scalars, and reading its routes is what allocates. `extract_all_feasible`, default `True`, skips the extraction entirely for callers that only ever read the best solution, in which case `.feasible_population` is `None` rather than empty.
- Errors raised by the solver now reach Python properly. Invalid caller data raises `ValueError` and I/O or parse failures raise `RuntimeError`, where the distance/demand scale and fleet-size checks previously surfaced as `SystemError: exception could not be translated!`.
- `RoutingSolution.n_routes` no longer converts the route list a second time.

## Packaging & Maintenance

- Updated the pinned HGS-CVRP commit, which adds the route-list constructor used for passing initial solutions and derives all library errors from `std::exception`.
- Moved musllinux wheels into a dedicated matrix entry. All three manylinux runners previously built the same musllinux wheels concurrently, compiling the extension redundantly and producing identical files that collided when artifacts were merged.
- Updated the action versions used by the build-and-publish workflow and added Python 3.15 wheels.

# v0.1.1

[Commit history since v0.1.0](https://github.com/mdealencar/HybGenSea/compare/v0.1.0...v0.1.1)

- Fixed the nanobind dependency to be resolved in a conda-forge-compatible way.

# v0.1.0

[Commit history since v0.0.1](https://github.com/mdealencar/HybGenSea/compare/v0.0.1...v0.1.0)

- Replaced the ctypes interface with a nanobind extension, and reworked the Python API around it: keyword-based `solve_cvrp`, `solve_cvrp_dist_mtx` and `solve_tsp` functions with algorithm parameters passed as keywords, alongside the existing `Solver` class.
- Solver calls release the Python GIL, so a solve no longer blocks other threads.
- Fixed argument conversion for array inputs, including read-only buffers, and corrected the module build for Windows linker compatibility.
- Stated the license in the project metadata, updated the project URLs and authors, and documented the conda-forge package in the README.
- Removed macos-13 from the build matrix, since GitHub retired it.

# v0.0.1

Initial HybGenSea release: the hygese fork was renamed and repackaged with scikit-build-core, built against HGS-CVRP v2.0.0, exposing the `nbIterTraces` and penalty-management algorithm parameters (`nbIterPenaltyManagement`, `penaltyDecrease`, `penaltyIncrease`), with wheels for multiple platforms.
