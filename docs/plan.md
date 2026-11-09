# Plan

Updated: 9 November 2026.

## Goal

First, fully reproduce Arpan's paper: its model, allocation calculations,
algorithms, and reported numerical experiments, with documented checks of the
mathematical results. Only after completing and reviewing the reproduction with
Arpan, ask whether its model or methods could support a finance application.
Finance is a possible later direction; the next study will be chosen after that discussion.

The [reproduction checklist](reproduction.md) records the scope, paper settings,
missing information, detailed tasks, and evidence needed to finish.

Use [project context](../.codex/context.md) to restore the student's constraints and decisions,
and [assessment and evidence](../.codex/assessment.md) to keep work aligned with the marking
criteria. The CS344 Project Coach skill supports this workflow.

## Assessment focus

The next submission is the progress report on 10 December 2026 at 12 noon.
Available effort until then is 8-10 hours per week, confirmed by the user on
8 November. Write and read critically alongside the reproduction work; full
paper reproduction does not need to be complete for this progress report.

The next technical task remains the first item under Current focus. Alongside
that work, develop the [progress-report draft](reports/report.tex), explain the
reproduction-first direction, and agree a draft/feedback date with Arpan. The
finance feasibility discussion comes after reproduction. See the assessment file
for sources and the current evidence gaps.

## How we maintain this plan

- Keep only the next three small tasks under Current focus. When I say "next",
  work on the first unfinished task there.
- Each task should have one clear outcome. Split it if it needs several independent changes.
- After each task, update the current state, record relevant checks or result links,
  and add the next small task from the reproduction checklist.
- Mark work complete only after checking its outcome. Add the actual completion
  date; leave future dates unscheduled. Preserve the Git dates in the history below.
- Keep detailed experiment settings and evidence in the reproduction checklist
  and saved results. Update their status when results are checked, rather than
  copying the full experiment list into this plan.
- At the end of each stage, check coverage and discrepancies against the paper.
  Record material changes of scope with a date and reason; discuss unresolved
  source details with Arpan. If a check fails, add a fix before continuing.
- Keep ideas for my own study in Later. Start them after the reproduction report
  is complete and the results have been reviewed with Arpan. At that point,
  discuss finance feasibility before choosing or planning a finance study.

The [project workflow](../AGENTS.md) records these rules for future coding sessions.

## Current focus

Generalize the single-class allocation rule. The first three tasks are:

- [ ] Validate the generalized rule for the paper's three traffic regimes and both speedup curves.
- [ ] Calculate the optimal mean execution-time benchmark for comparison with simulations.
- [ ] Write short notes explaining the generalized allocation rule and its assumptions.

## Reproduction roadmap

- [ ] Generalize and validate the single-class allocation rule and benchmark.
- [ ] Check the paper's mathematical results and document their assumptions.
- [ ] Finish shared experiment execution, settings, saved evidence, and uncertainty analysis.
- [ ] Reproduce every curve in Figure 2(a) and Figure 2(b).
- [ ] Reproduce all job-size distribution cases in Table I.
- [ ] Implement and validate Section VI, including Algorithm 1 and multiple job classes.
- [ ] Complete the reproduction report, resolve discrepancies, and review it with Arpan.

## What we have now

- A tested event-driven [Simulator](../scheduling/simulator.py), with [Job](../scheduling/job.py),
  [ServerPool](../scheduling/server_pool.py), and [Statistics](../scheduling/statistics.py) in their own modules; two allocation policies.
- [Logger](../scheduling/logger.py) creates and stores immutable [Event](../scheduling/event.py)
  snapshots, with attributes such as `event.time` and `event.kind`. Event retention
  can be disabled with `record_events=False` without changing measurements.
  Conservation and event-order assertions remain in tests.
- Workloads contain immutable `Job(id, size, arrival_time)` objects. Each run
  has a ServerPool that owns capacity, job execution, and a private
  [CompletionQueue](../scheduling/completion_queue.py). Simulator owns the clock
  and event order. Statistics owns total counts, measurements after warm-up,
  and allocation counts; main.py reads those summaries directly.
  Warm-up follows arrival order, including when supplied IDs are nonconsecutive.
- Default model: 100 servers, Poisson arrivals at rate `0.8 * servers`, exponential
  job sizes with mean 1, and speedups `(1, 1.8, 2.5, 3, 3.4)`.
- main.py derives arrival intensity as `NORMALIZED_LOAD * SERVERS / MEAN_JOB_SIZE`.
- RandomizedPolicy accepts an explicit target distribution and seed. Each
  randomized run calculates its targets and probabilities from the configured load and speedups;
  the policy samples once per arrival, including blocked and single-target cases.
- [Optimal target selection](../scheduling/allocation.py) now implements Theorem 1
  as a pure function of load and speedups, including boundary and linear cases.
  Its baseline result is `(3, 4)`.
- `optimal_allocation_probabilities()` now calculates the corresponding
  probabilities from equations (8)-(9) and Section IV, returning approximately
  `(0.625, 0.375)` for the baseline. It handles single targets and normalizes
  floating-point results; both allocation helpers now configure randomized runs.
- main.py holds plain configuration constants: server count, normalized load,
  mean size, speedups, both seeds and run lengths. ModelSettings and config.py
  were removed on 9 November. Simulator and ServerPool take server count and
  speedups explicitly. main.py validates configuration once before generating
  jobs; internal components trust those settings and valid generated jobs.
  Runtime guards retain allocation limits, arrival-time ordering and finite
  completion times. Job is a frozen dataclass without per-object validation.
- One application entry point: `main.py`. It generates a workload, calculates
  the randomized allocation distribution, runs Simulator directly, and prints
  blocking probability and mean execution time. Workload seed 0 and policy seed
  10,000 retain the previous randomized baseline. Event retention is disabled.
- Comparison execution, across-run analysis, workload fingerprints, and
  ExperimentSettings were removed on 9 November at the user's request. Repeated
  experiments and saved evidence are deferred until needed for reproduction.
- Latest check: 77 automated tests pass, including startup configuration checks,
  target selection checked
  against exact LP vertices for 45 configurations and probability feasibility
  and optimality checked for 60 configurations, configured weighted sampling,
  model-driven policy changes, seeded replay, pool lifecycle operations,
  warm-up and allocation counts, independent summary snapshots, and identical
  measurements with event retention disabled.
- An initial [progress-report draft](reports/report.tex) with the current model and
  implementation, a paper reference, and visible notes for unfinished sections.

Run from the project folder:

```bash
.venv/bin/python main.py
```

All old runner scripts, saved results, figures, and generated experiment reports
were removed on 8 November at the user's request. There are currently no saved
experiment outputs. Full paper reproduction still needs fresh experiment evidence.

## What we completed

Dates through 6 November show when the work was committed to Git. Work may
have been completed earlier; milestones committed together share a date.

- [x] 3 November 2026: Define the [model](model.md).
- [x] 3 November 2026: Set up the project.
- [x] 3 November 2026: Build the greedy event loop with Job, ServerPool, and Simulator.
- [x] 3 November 2026: Add random arrivals and job sizes.
- [x] 4 November 2026: Add Statistics, warm-up, blocking probability, and mean execution time.
- [x] 6 November 2026: Run the 100-server greedy experiment and warm-up/run-length checks.
- [x] 6 November 2026: Implement the paper's randomized rule for the current parameters,
  compare it with greedy on matched workloads, and check its sensitivity.
- [x] 6 November 2026: Compare RandomizedPolicy with 25, 50, 100, 200, 500, and 1,000 servers.
- [x] 6 November 2026: Save reproducible results, reports, and PNG/SVG figures.
- [x] 6 November 2026: Check correctness with 53 passing automated tests at that commit.

The following dates record when later implementation and project work was completed:

- [x] 7 November 2026: Add ModelSettings with server count, load, mean size, and speedups.
- [x] 7 November 2026: Add ExperimentSettings with seeds, run lengths, server counts,
  sensitivity thresholds, and confidence level.
- [x] 7 November 2026: Validate both settings objects.
- [x] 7 November 2026: Pass configured speedups into the simulator and jobs;
  derive the maximum allocation from the curve.
- [x] 8 November 2026: Organize code into `scheduling/`, `scripts/`, and `tests/`;
  extract shared helpers and update imports, paths, source snapshots, and commands.
  All 79 tests, examples, export checks, and plotting checks passed.
- [x] 8 November 2026: Define the reproduction goal, plan maintenance rules, and
  initial paper coverage checklist; add workflow instructions for future sessions.
  Known gaps remain open in that checklist.
- [x] 8 November 2026: Create the CS344 Project Coach skill, verified assessment
  notes, and a context briefing; record the 8-10-hour weekly budget and evidence gaps.
- [x] 8 November 2026: Ignore local assistant instructions, configuration, skills,
  and coaching notes in Git; verify that project documentation and results remain included.
- [x] 8 November 2026: Simplify the README to run commands, experiments, tests,
  and documentation links; check that the linked files and commands exist.
- [x] 8 November 2026: Delete the README at the user's request.
- [x] 8 November 2026: Remove `run_fixed.py`, `run_random.py`, and the unused
  `reporting.py` helper; move shared test inputs into `tests/fixtures.py` and
  check all 79 tests. Keep the experiment and plotting commands for reproducibility.

- [x] 8 November 2026: Remove all runner/plotting scripts, saved outputs, generated
  result reports, and the plotting dependency. Keep `main.py` as the single entry
  point, consolidate run/analysis helpers in the package, and pass all 80 tests.
- [x] 8 November 2026: Create the initial [progress-report draft](reports/report.tex).
  Check compilation with pdfLaTeX and inspect all four rendered pages. Keep build
  files outside the repository; numerical reproduction evidence remains pending.
- [x] 8 November 2026: Group LaTeX sources in `docs/reports/` and the crest in
  `docs/reports/assets/`; move local coaching notes to `.codex/`. Update links,
  coach references and LaTeX paths, and check both documents still compile.
- [x] 8 November 2026: Clarify the research sequence in the plan, context,
  reproduction checklist, workflow instructions and report: finish full paper
  reproduction first, then discuss finance feasibility with Arpan.

- [x] 8 November 2026: Give Job, ServerPool, and Statistics their own modules;
  rename the event-loop module to `scheduling/simulator.py` and its test file
  to `tests/test_simulator.py`. Update imports, pass all 80 tests with
  `.venv/bin/python -B -m unittest discover -s tests -q`, and confirm that
  `.venv/bin/python -B main.py` prints exactly the same seeded baseline summary.

- [x] 8 November 2026: Add an immutable Event dataclass in `scheduling/event.py`;
  use Event objects in the simulator log and update experiment helpers and
  existing tests to read their attributes. All 80 tests pass with
  `.venv/bin/python -B -m unittest discover -s tests -q`;
  `.venv/bin/python -B main.py` prints the same seeded baseline summary.

- [x] 8 November 2026: Simplify `Simulator.record()` to append an Event snapshot.
  Remove its per-event bookkeeping checks; retain input validation and the
  independent conservation and event-order checks in existing tests. All
  80 tests pass with `.venv/bin/python -B -m unittest discover -s tests -q`;
  `.venv/bin/python -B main.py` prints the same seeded baseline summary.

- [x] 8 November 2026: Make Job an immutable input containing only `id`, `size`,
  and `arrival_time`. Generate jobs directly and keep each run's allocations
  and completion times in its completion heap. Update measurement to use arrival
  order for warm-up and include IDs in workload fingerprints. All 85 tests pass
  with `.venv/bin/python -B -m unittest discover -s tests -q`. Compare complete
  event traces and numerical measurements against the previous implementation
  for seeds 0, 7, and 42 with both policies, plus simultaneous and zero-duration
  arrivals; all match exactly. `.venv/bin/python -B main.py` prints the same baseline.

- [x] 8 November 2026: Extract Logger for immutable event snapshots and
  CompletionQueue for scheduling and retrieving future completions. Keep clock
  advancement, arrival handling, and completion handling in Simulator; move
  measurement-summary construction into `Statistics.summary()`. All 85 existing
  tests pass with `.venv/bin/python -B -m unittest discover -s tests -q`.
  Complete event traces, statistics, fingerprints, and experiment outputs match
  the previous implementation for seeds 0, 7, and 42 with both policies;
  `.venv/bin/python -B main.py` prints the same seeded baseline summary.

- [x] 8 November 2026: Give ServerPool ownership of starting/completing jobs,
  capacity, speedup calculations, and its private CompletionQueue. Keep only
  clock advancement, event ordering, and coordination in Simulator. Move whole-run
  counts and measured allocation frequencies into Statistics; remove measurement
  calculations from the experiment helper's event-log processing. Allow Logger
  retention to be disabled through `record_events=False`. All 92 tests pass with
  `.venv/bin/python -B -m unittest discover -s tests -q`. Check 14 baseline cases
  covering both policies, three seeds, custom IDs/curves, warm-up, empty inputs,
  and simultaneous/zero-duration arrivals: event traces, original measurements,
  allocation frequencies, fingerprints, and experiment outputs are unchanged.
  Disabling event retention leaves every measurement unchanged, and
  `.venv/bin/python -B main.py` prints the same seeded baseline summary.

- [x] 8 November 2026: Add the derived `ModelSettings.arrival_rate` property and
  use it in `main.py`, experiment workload generation, and returned metadata.
  All 92 tests pass with `.venv/bin/python -B -m unittest discover -s tests -q`;
  `.venv/bin/python -B main.py` prints the same seeded baseline summary. Check
  both policies with 40 servers, load 0.6, seed 7, 1,000 arrivals and 100 warm-up
  arrivals: doubling mean job size from 1 to 2 halves arrival rate from 24 to 12,
  doubles execution times, and preserves allocations and blocking probability.

- [x] 9 November 2026: Implement `optimal_allocation_targets()` in
  [allocation.py](../scheduling/allocation.py) using Theorem 1's efficiency
  thresholds. Return a single target or two neighbours, including linear,
  light-load, and equality cases; handle division rounding without collapsing
  loads just below 1 into the excluded unit-load boundary. Add nine tests in
  [test_allocation.py](../tests/test_allocation.py), including an independent
  enumeration of all one- and two-target vertices of LP (7) using exact fractions
  for five curves and nine loads. All 101 tests pass with
  `.venv/bin/python -B -m unittest discover -s tests -q`;
  `.venv/bin/python -B main.py` prints the same seeded baseline summary.
  Probabilities and connection to RandomizedPolicy remain unfinished.

- [x] 9 November 2026: Add `optimal_allocation_probabilities()` alongside target
  selection in [allocation.py](../scheduling/allocation.py). Use equations
  (8)-(9) and Section IV's `p_i = s_i * y_i / load`; return probability 1 for a
  single target and normalize paired weights for rounding. Add seven probability
  tests in [test_allocation.py](../tests/test_allocation.py), covering the baseline,
  changed model inputs, both sides of boundaries, loads near 1, and comparison
  with exact LP minima for five curves and twelve loads (60 configurations).
  Check nonnegative finite weights, sums of 1, and capacity feasibility.
  All 108 tests pass with `.venv/bin/python -B -m unittest discover -s tests -q`;
  `.venv/bin/python -B main.py` prints the same seeded baseline summary.
  RandomizedPolicy still uses its fixed baseline; connecting these helpers is next.

- [x] 9 November 2026: Make RandomizedPolicy accept explicit targets,
  probabilities, and a seed; remove its fixed 3/4 branch. Validate and copy the
  distribution, then sample one target per arrival and cap it by idle capacity.
  Calculate each randomized experiment's distribution from ModelSettings in
  `run_policy()`. Update direct constructor calls and add eight tests for generic
  distributions, single/zero-weight cases, invalid inputs, model changes, and replay.
  All 116 tests pass with `.venv/bin/python -B -m unittest discover -s tests -q`.
  Compare complete event traces and experiment summaries with the previous
  implementation for both policies, seeds 0, 7, and 42, 1,100 arrivals and 100
  warm-up arrivals: all six cases match exactly. `.venv/bin/python -B main.py`
  also prints the same seeded baseline summary. Full paper-regime validation
  and the execution-time benchmark remain pending.

- [x] 9 November 2026: Simplify `scheduling/experiments.py`.
  Make `run_trial(model, experiment, seed)` generate one workload and compare both
  policies using the supplied settings. Keep `run_policy()` for supplied jobs;
  remove its metadata-only workload seed and the manually flattened result schema.
  Update main.py, analysis and existing tests to consume the simulator's counts
  and nested Statistics summary. Keep seeds, model settings, workload fingerprints
  and consistency checks; calculate the fingerprint once per trial and disable
  event retention by default. All 115 tests pass with
  `.venv/bin/python -B -m unittest discover -s tests -q`. Twelve seeded runs
  (both policies, seeds 0/7/42, baseline and a changed model) preserve every
  count, allocation, metric and metadata value after accounting for the new
  schema. main.py output is unchanged; across-run analysis accepts trial results.
  Repeated execution and saved paper-reproduction evidence remain unfinished.

- [x] 9 November 2026: At the user's request, remove the comparison layer and
  keep one direct simulation in [main.py](../main.py). Remove experiments.py,
  analysis.py and ExperimentSettings, along with their specific tests. Move four
  useful model-integration and warm-up checks into the simulator/statistics tests.
  Keep the core simulator, allocation calculations and both policy classes.
  All 87 remaining tests pass with `.venv/bin/python -B -m unittest discover -s tests -q`;
  the direct run preserves every statistic of the previous randomized baseline.
  Defer repeated-run infrastructure; the next three tasks focus on allocation
  validation, the mathematical benchmark and explanation notes.

- [x] 9 November 2026: Make [main.py](../main.py) the configuration holder as
  requested by the user. Replace ModelSettings with plain constants and derive
  the arrival rate in main(). Remove config.py and move its validation checks
  to allocation helpers, ServerPool and WorkloadGenerator. Require explicit
  server count and speedups when constructing the simulator, with no imports
  from main.py in reusable modules. Move the configuration tests to the
  relevant component tests. All 86 tests pass with
  `.venv/bin/python -B -m unittest discover -s tests -q`; the main.py result and
  printed output are unchanged, and twelve complete seeded traces match the
  previous implementation exactly.

- [x] 9 November 2026: Centralize configuration validation once in main.py, as
  requested by the user. Check capacity, load, mean size, derived arrival rate,
  run lengths and speedup assumptions before generating jobs. Remove repeated
  constructor, policy-input, job-type and ID checks; Job now contains only its
  three immutable fields. Keep the runtime allocation, arrival-order and finite
  completion checks, mathematical tests, conservation, warm-up, replay and
  event-retention checks. Move configuration tests to test_main.py and remove
  tests for the retired internal validation contracts. All 77 tests pass with
  `.venv/bin/python -B -m unittest discover -s tests -q`; twelve complete seeded
  traces and main.py's result/output match the previous implementation exactly.

## Later: discuss finance feasibility

After full reproduction and review with Arpan:

- Ask whether the paper's model or methods could support a finance application.
- If feasible, agree a specific research question, model and success criteria
  before creating a finance implementation plan.
- Otherwise, agree another original study. Existing candidate ideas include
  inaccurate arrival-rate estimates, learning parameters, or additional load cases.

Finance modelling and implementation are outside the current reproduction work.

## Scope decisions

- 8 November 2026: Expand the previous single-case study into full paper
  reproduction before starting an original study, as requested. Replace the
  proposed custom load grid (0.6, 0.8, 0.95) with the paper's experiment cases;
  keep the existing results as pilot evidence.
- 8 November 2026: Add assessment-aware prioritization and protected reading/writing
  time, following the user's request to maximize the module mark. Keep the
  reproduction-first research goal and review its feasibility with Arpan.

- 8 November 2026: Replace the old experiment/plotting runners and all saved
  results with one main entry point, explicitly requested by the user. Preserve
  the research goal; rebuild experiment evidence through this entry point later.
- 8 November 2026: User clarified that finance is uncertain. Complete full paper
  reproduction before asking Arpan about financial applicability. Keep the
  original specification as the historical proposal; document the current
  sequence in the progress report without claiming supervisor approval.
