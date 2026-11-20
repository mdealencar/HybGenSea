# Unreleased

[Commit history since v0.3.0](https://github.com/mdealencar/HybGenSea/compare/v0.3.0...HEAD)

## Important Changes

- Wheels are published for free-threaded CPython 3.14t and 3.15t, and importing the package keeps the GIL disabled there. Solves started from several threads run fully in parallel, and returned results can be read from any thread.
- The fields of the internal `_core._PySolution` result are now read-only; `RoutingSolution` is unaffected.

## Packaging & Maintenance

- The HGS-CVRP sources are now a git submodule and are shipped inside the sdist, so building from the sdist no longer needs git or network access to fetch them. When building from a git checkout, initialize the submodule first (`git clone --recurse-submodules`, or `git submodule update --init`).
- The build compiles only the HGS-CVRP objects that the extension links, and no longer builds the unused upstream shared library.
- The package version is taken from the git tag by setuptools-scm instead of being set in `pyproject.toml`, and is available as `hybgensea.__version__`.
- `numpy` is now declared as a dependency; it was always imported but was missing from the package metadata.
- The HGS-CVRP license is included in the sdist and wheels.
- The GitHub workflows are reorganized by purpose. `Test` runs on each push and pull request: it builds the sdist, installs the package from it and runs the tests on Linux, Windows and macOS. `Build` makes the sdist and every wheel and tests each wheel; it can be run by hand to check a release without publishing. `Release` runs `Build` on version tags, then publishes to PyPI and creates a GitHub Release with the sdist and wheels attached.

# v0.3.0

[Commit history since v0.2.0](https://github.com/mdealencar/HybGenSea/compare/v0.2.0...v0.3.0)

## Important Changes

- The local search handles asymmetric distance matrices better: it reverses a whole route, or a route after its first client, whenever that is cheaper. When the asymmetry is confined to the depot connections (e.g. an open CVRP with free return legs, as in `dist_mtx[:, 0] = 0`), SWAP* also prices each route in its cheaper orientation; clients whose connections with the depot are free both ways (depot clones) are left out of that pricing.
- Solutions for asymmetric distance matrices therefore differ from those of v0.2.0 at the same seed. In benchmarks under a CPU-time limit, they were about 0.02% cheaper on average for general asymmetric matrices, and no different for an open CVRP with free return legs, whose iterations take up to about 1% more time. Coordinate inputs and symmetric matrices give the same solutions as before, at no measurable extra time.
- Runs stopped by `nbIter` (iterations without improvement) on asymmetric matrices may last more iterations than before; runs stopped by `timeLimit` are unaffected.

## Packaging & Maintenance

- Updated the pinned HGS-CVRP commit, which adds the route reversal moves and the orientation-aware SWAP*.

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
