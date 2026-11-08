# Plan

Updated: 8 November 2026.

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

- [ ] Derive arrival rate in ModelSettings from load, server count, and mean job size.
- [ ] Find the optimal single target or two neighbouring targets in `scheduling/allocation.py`.
- [ ] Calculate target probabilities from the model settings.

## Reproduction roadmap

- [ ] Generalize and validate the single-class allocation rule and benchmark.
- [ ] Check the paper's mathematical results and document their assumptions.
- [ ] Finish shared experiment execution, settings, saved evidence, and uncertainty analysis.
- [ ] Reproduce every curve in Figure 2(a) and Figure 2(b).
- [ ] Reproduce all job-size distribution cases in Table I.
- [ ] Implement and validate Section VI, including Algorithm 1 and multiple job classes.
- [ ] Complete the reproduction report, resolve discrepancies, and review it with Arpan.

## What we have now

- A tested event-driven simulator with Job, ServerPool, Statistics, and two policies.
- Default model: 100 servers, Poisson arrivals at rate `0.8 * servers`, exponential
  job sizes with mean 1, and speedups `(1, 1.8, 2.5, 3, 3.4)`.
- Randomized targets remain hardcoded at 3/4 with probabilities 0.625/0.375;
  calculating them from settings is still pending.
- ModelSettings and ExperimentSettings validate inputs. Run helpers use the
  actual model settings and return measurements without writing files.
- One application entry point: `main.py`. It compares both policies on one
  shared seeded workload using the first configured seed and prints a summary.
- Reusable run functions are in `scheduling/experiments.py`; across-run summaries
  and comparisons are in `scheduling/analysis.py`; checks are in `tests/`.
- Latest check: 80 automated tests pass, including custom model settings in run helpers.
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

Dates show when the work was committed to Git. Work may have been completed
earlier; milestones committed together share a date.

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

The following dates record completed implementation work after the latest commit:

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
