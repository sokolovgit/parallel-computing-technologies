## Learned User Preferences

- For Java labs in this repo, prefer plain `javac`/`java` with a simple `src`/`out` layout and avoid Maven/Gradle unless explicitly required.
- Run and document build and run commands from the relevant project directory using the editor terminal (e.g. `lab4/project`).
- Lab reports are often written in Ukrainian and modeled on prior labs in the same course (structure, headings, media layout).
- For the course-work explanatory note, prefer editing split section files under `course-work/docs/sections/` and small targeted diffs rather than large reflows in a single monolithic markdown file.
- For formal reports here: cite sources in the body beyond the introduction; reference every figure and table in the prose.

## Learned Workspace Facts

- The workspace mixes semester labs (`lab1`–`lab4`) and `course-work/` (bitonic parallel sort, benchmarks, defense presentation, and report materials).
- `lab3/project` is matrix multiplication coursework with a `justfile` for compile, verification, benchmarks, and plotting.
- `lab4/project` holds Fork/Join lab sources under `src/lab4/` (`lab4.common`, `lab4.task1`–`task3`, …); data dirs include `data/samples/`, gitignored `data/corpus/`, `data/task3/` for common-words demo; `justfile` runs `task1`–`task3`, benchmark/plot recipes for tasks 1–2, `corpus-fetch`; results in `results/`, figures via `plots/` (matplotlib).
