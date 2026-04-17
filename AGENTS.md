## Learned User Preferences

- For Java labs in this repo, prefer plain `javac`/`java` with a simple `src`/`out` layout and avoid Maven/Gradle unless explicitly required.
- Run and document build and run commands from the relevant project directory using the editor terminal (e.g. `lab4/project`).
- Lab reports are often written in Ukrainian and modeled on prior labs in the same course (structure, headings, media layout).
- For the course-work explanatory note, prefer editing split section files under `course-work/docs/sections/` and small targeted diffs rather than large reflows in a single monolithic markdown file.
- For formal reports here: cite sources in the body beyond the introduction; reference every figure and table in the prose.
- For lab reports aimed at benchmarks and plots, prefer hardcoded run parameters and a small CLI surface instead of many tunable knobs.
- When adding comments in course Java sources, write them in English.
- For lab reports that will be copied into Word (or exported to DOCX), prefer Markdown math with `$...$` and `$$...$$` (and typical Markdown→DOCX tools) rather than relying on chat-style `\(...\)` / `\[...\]` alone.
- For mpi4py code under a nested `uv` project, point Cursor’s Python interpreter at that project’s `.venv` (e.g. `lab7/project/.venv`) so Pylance/Pyright resolves `mpi4py`; a repo-root or system interpreter often still resolves `numpy` but not MPI-only installs.
- For benchmark plots with many algorithms and process counts, keep series distinguishable (e.g. marker or line style per algorithm, color per process count) so overlapping curves stay readable.

## Learned Workspace Facts

- The workspace mixes semester labs (`lab1`–`lab7`) and `course-work/` (bitonic parallel sort, benchmarks, defense presentation, and report materials).
- Lab documentation often splits the written assignment under `labN/docs/task/` and lecture PDFs under `labN/docs/materials/` (used as the main theory sources when building knowledge notes or reports).
- `lab3/project` is matrix multiplication coursework with a `justfile` for compile, verification, benchmarks, and plotting.
- `lab4/project` holds Fork/Join lab sources under `src/lab4/` (`lab4.common`, `lab4.task1`–`task4`, …); data dirs include `data/samples/`, gitignored `data/corpus/`, `data/task3/`, `data/task4/`; `justfile` runs `task1`–`task4`, benchmark/plot recipes, `corpus-fetch`, `print-java` (via `scripts/dump_lab4_java.sh`); results in `results/`, figures via `plots/` (matplotlib).
- `lab5/project` is discrete-event / multi-channel queueing simulation coursework under `src/lab5/` (`lab5.smo`, `lab5.task1`–`task3`); `justfile` provides `task1`, `task1-plots` (CSV + matplotlib), `task2`, `task3`; results and figures land under `project/results/` (and task-1 figures via `plots/`).
- `lab6/project` is MPI (Open MPI) coursework: C under `src/`, output in `bin/`; `justfile` has `task1`–`task3`, `task4-bench` / `task4-plot` (run `uv sync` + `uv run lab6-bench` / `lab6-plot` from `plots/`, pyproject like lab4 plots; default bench sweep N=100..1000 step 50, np=2..8, runs=10), `print-c` (via `scripts/dump_lab6_c.sh`, like lab4 `print-java`), `compile-commands` (`scripts/gen_compile_commands.py`). Report draft in `lab6/docs/report/lab6.md`.
- `mkr2/` holds midterm-style exercises: Fork/Join Java under `mkr2/java/`, mpi4py MPI under `mkr2/mpi/` (`pyproject.toml` with `mpi4py`/`numpy`, `uv sync`, run with `mpirun` + `uv run python` from that directory).
- `lab7/project` is MPI collective matrix multiply in Python: package `matrix_multiplication` under `src/matrix_multiplication/` (`implementations/` holds `p2p`, `collective_sbg`, `p2p_gatherv`, `allgatherv`; base `MatrixMultiplyBase`, `ALGOS` in `registry.py`); `benchmarks/` for `demo`, `bench_runner`, `run_benchmarks`; `plots/` for matplotlib figures; `justfile` `demo` / `bench-plot` → CSV/PNG under `lab7/docs/results/`; `uv sync` from `lab7/project`. Report `lab7/docs/report/lab7.md`, knowledge base `lab7/docs/knowledge-base.md`.
