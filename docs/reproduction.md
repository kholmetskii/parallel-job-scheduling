# Paper reproduction checklist

Updated: 9 November 2026.

Source: Mukhopadhyay et al., *On Optimal Server Allocation for a Loss System
With Moldable Jobs*, IEEE Transactions on Networking, 34, 384-397 (2026).
[Paper DOI](https://doi.org/10.1109/TON.2025.3598595).

Use [plan.md](plan.md) for the next three tasks. Use this file for detailed
coverage, source questions, and links to evidence. This is a checklist for work
to complete, not a statement that the paper has already been reproduced.

## Scope and completion

Reproduce the model and allocation algorithms, independently check the analytical
calculations, work through the main proof arguments, and regenerate the reported
numerical experiments. Section VI is included even though Figure 2 and Table I
do not provide a separate multiple-class experiment to copy.

The reproduction is complete when all targets below have checked evidence,
every reported numerical case has been compared with the paper, assumptions and
remaining differences are explained, and the report has been reviewed with Arpan.
Simulations illustrate asymptotic results; they do not prove the theorems.

Finance modelling is outside this reproduction. Only after completion and review
with Arpan will we discuss whether a finance application is feasible. That later
decision does not change the reproduction targets below.

For each target, record:

- Status: **Not started**, **Partial**, or **Verified**, plus the date checked.
- The paper section, equation, figure, or table being reproduced.
- Actual settings, source of each setting, and any assumptions or clarifications.
- Code/test references, run commands, saved data, and comparison reports.
- Discrepancies and the next action needed to resolve them.

"Verified" means the outcome has been checked against its stated acceptance
criteria. For experiments, code completion alone is insufficient. Agree numerical
comparison criteria before the full runs; use uncertainty and published rounding
when available. Do not require identical random estimates when seeds/raw data
are unavailable, or treat qualitative agreement alone as full numerical agreement.

## Coverage and evidence

| Target | Current status | Evidence and work remaining |
| --- | --- | --- |
| Section II: loss-system model | Partial | [Baseline model](model.md), [simulator](../scheduling/simulator.py) and [tests](../tests/test_simulator.py) exist. Immutable [Job](../scheduling/job.py) inputs feed a [ServerPool](../scheduling/server_pool.py) that owns job execution and its private CompletionQueue; Simulator owns time and ordering. Statistics owns all counts and measurements, independently of Logger retention (8 November). All 77 tests pass; seeded baseline traces and measurements are preserved for both policies, and disabling event retention preserves every measurement. main.py derives the arrival rate from its configured load, capacity and mean job size; a check with both policies confirms that doubling mean size halves the rate, doubles execution times, and preserves allocations and blocking. Document the full parameterized model. |
| Section III: LP (7), Proposition 1, Theorem 1 | Partial | [Allocation helpers](../scheduling/allocation.py) implement target selection and use equations (8)-(9) to calculate the selected state components and probabilities (9 November). [Sixteen allocation tests](../tests/test_allocation.py) cover boundaries, linear/light-load cases, and exact LP vertex checks: target selection for 45 configurations and probability feasibility/optimality for 60 configurations. Further mathematical checks, a reusable execution-time benchmark, and proof notes remain pending. |
| Section IV: greedy and greedy(p*) | Partial | RandomizedPolicy now samples targets and probabilities calculated from the configured load and speedups directly in main.py (9 November). Tests check configured distributions, single-target cases, changes in load/speedups, event order, and seeded replay. Earlier checks matched six baseline event traces and summaries; the direct main.py run preserves every statistic of the previous randomized baseline. Checking all required paper settings and collecting new experiment evidence remain pending. |
| Section V and Appendices A-E: proof arguments | Not started | Write checked notes on assumptions, proof steps, and what simulations can establish. |
| Figure 2(a): blocking probability | Not started | Earlier pilot outputs were removed on 8 November. All published curves and sizes need new saved evidence. |
| Figure 2(b): accepted-job execution time | Not started | Earlier pilot outputs were removed on 8 November. All published curves and sizes need new saved evidence. |
| Table I: job-size distributions | Not started | Reproduce all 24 configurations and both reported metrics. |
| Section VI: heterogeneous workloads and Algorithm 1 | Not started | Implement class settings, job creation, capacity optimization, policies, and validation. |
| Sections I and VIII: motivation, conclusions and limits | Not started | Explain the research question, reproduce supported conclusions, and distinguish proposed future work. |

Update this table when checked evidence becomes available. Add per-case rows or
links to result reports as each experiment stage starts.

## Paper experiment settings

Section VII reports 100 repetitions, each simulating the first 5 million job
arrivals, with maximum parallelism 5. All listed job-size distributions have mean 1.
Earlier ten-seed pilot outputs were removed on 8 November at the user's request.
The current main.py runs the randomized policy once and prints its results.
Comparison and repeated-run infrastructure are deferred at the user's request
(9 November 2026); they will be needed when collecting reproduction evidence.

Arrival rate is `n * lambda(n)`, with `lambda(n) = 1 - beta * n**(-alpha)`.

For mean inherent job size `m`, the implementation uses
`arrival_rate = NORMALIZED_LOAD * SERVERS / MEAN_JOB_SIZE` in main.py.
This reduces to the paper's `n * lambda(n)` when `m = 1`, as in its experiments.
The traffic parameters are:

| Regime | alpha | beta |
| --- | ---: | ---: |
| Mean-field | 0 | 0.2 |
| Halfin-Whitt | 1/2 | 0.1 |
| Super-Halfin-Whitt | 2/3 | 0.1 |

Speedups are linear `(1, 2, 3, 4, 5)` or sublinear `(1, 1.8, 2.5, 3, 3.4)`.

Figure 2's legends show five series in each panel: greedy(p*) with sublinear
speedups in all three regimes; greedy(p*) with linear speedups in the mean-field
regime; and greedy with sublinear speedups in the mean-field regime. Match those
series and each panel's system sizes. Additional comparisons can be useful checks
but should be labelled separately.

Table I uses 4,000 servers, both speedup curves, all three regimes, and four
job-size distributions: exponential, deterministic, Mixed-Erlang, and Pareto.
This gives 24 configurations, each reporting blocking and mean execution time.
The stated Pareto CDF is `1 - (3*y)**(-3/2)` for `y >= 1/3`, and zero below.
The Mixed-Erlang description gives probabilities 0.4 and 0.6; confirm its full
construction before implementing it.

## Source questions to resolve

- [ ] Recover the exact system-size points used in each Figure 2 panel, preferably
  from author code/data. Axis tick labels alone do not specify all simulated points.
- [ ] Ask Arpan about original code/data, seeds, initialization, warm-up, and
  measurement conventions. Clarify whether any warm-up is included in the stated
  5 million arrivals; keep our protocol and any differences explicit.
- [ ] Confirm the Mixed-Erlang distribution's phase/mixture construction and rates.
- [ ] Check Section VI's job-size/service-rate notation and Algorithm 1's capacity
  update against optimization problems (21)-(23) before translating them into code.
- [ ] Agree documented assumptions for unreported details if original information
  cannot be recovered, and label the resulting reproduction accordingly.

These questions do not prevent work on the general single-class implementation.
Record answers and their source here when received; do not invent missing settings.

## Generalize the single-class implementation

- [x] Derive arrival rate from normalized load, server count, and mean job size.
  Completed 8 November 2026; the formula is now directly in main.py (9 November).
- [x] Find the optimal single target or two adjacent targets in `scheduling/allocation.py`.
  Completed 9 November 2026; target selection matches exact LP minima in 45 cases.
- [x] Calculate their probabilities from the model settings.
  Completed 9 November 2026; feasibility and LP optimality checked in 60 cases.
- [x] Make RandomizedPolicy use the calculated targets and probabilities.
  Completed 9 November 2026; model changes determine the experiment's distribution.
- [ ] Calculate the theoretical mean execution-time benchmark.
- [ ] Check the known case: targets 3/4, probabilities 0.625/0.375, benchmark 0.375.
- [x] Test single-target cases, boundary loads, linear speedups, and invalid inputs.
  Completed 9 November 2026; allocation, policy, and experiment tests pass.
- [x] Recheck the 100-server baseline after generalizing the policy; earlier saved outputs have been removed.
  Completed 9 November 2026; six event traces/summaries and main.py output match
  the implementation immediately before policy integration. New published-result
  reproduction evidence remains pending.

## Check the mathematical results

- [ ] Explain the normalization, state variables, flow conservation, and Little's law
  in Section II and equations (3)-(7).
- [ ] Work through Proposition 1 and Theorem 1, including the one/two-target cases;
  verify feasible solutions and objective values independently on small examples.
- [ ] Check the conversion from optimal state y* to arrival probabilities p* and D*.
- [ ] Work through Theorem 2, Section V, and Appendices A-E; record the assumptions
  and bounds, including conditions involving n, d(n), alpha, and beta.
- [ ] Investigate unclear steps or apparent notation inconsistencies with Arpan;
  record resolutions instead of silently changing the paper's model.

## Finish the experiment infrastructure

- [x] Validate configuration once at startup and trust valid internal data.
  Completed 9 November 2026 at the user's request. main.py checks model/run
  inputs before generating jobs; Job and internal components no longer repeat
  those checks. Keep runtime allocation limits, arrival-time ordering and finite
  completion checks. All 77 tests pass, including configuration checks at the
  entry point and the existing mathematical/conservation tests. Twelve seeded
  traces and main.py's result/output are unchanged.
- [x] Keep configuration in main.py as plain constants and pass inputs explicitly
  to the simulator and policies. Completed 9 November 2026; remove ModelSettings
  and config.py, retain validation in the components that use each input, and
  pass all 86 tests. main.py output and all baseline statistics are unchanged;
  twelve complete seeded traces match the previous implementation.
- [x] Run one seeded simulation directly through main.py. Completed 9 November 2026.
  At the user's request, remove experiments.py (including run_trial/run_policy),
  analysis.py, workload fingerprinting and ExperimentSettings. Keep both policy
  classes, the allocation calculations and the core simulator/statistics checks.
  All 87 remaining tests pass; the direct randomized run preserves every
  statistic from the previous baseline. The dated history remains in plan.md.
- [x] Keep whole-run counts and measured allocation frequencies in Statistics,
  independent of event retention; main.py consumes its summaries.
  Check 92 tests and 14 comparison cases, including `record_events=False`.
  Completed 8 November 2026.
- [ ] When reproduction runs begin, add repeated execution and across-run analysis
  through main.py using the required cases and seeds.
- [ ] Save actual settings, both random seeds, source revision/fingerprints, run
  lengths, counts, and per-run metrics with each experiment.
- [ ] Generate report descriptions and chart labels from saved settings.
- [ ] Add uncertainty estimates across independent replications, with a method
  appropriate to the job-size distribution and the configured confidence level.
- [ ] Pilot warm-up, measurement length, runtime, and memory for the paper's cases;
  support long runs without retaining every event if necessary, and check that
  any execution optimization preserves the measured results.
- [ ] Save new evidence when running reproduction experiments; previous pilot outputs were removed during cleanup.

## Reproduce Figure 2

- [ ] Record the exact case list, system sizes, and agreed measurement protocol.
- [ ] Calculate load, allocation probabilities, and theoretical benchmarks for each n.
- [ ] Run small checks for every curve before starting the full experiment budget.
- [ ] Run the reported cases with 100 independent repetitions and the paper's
  5-million-arrival length, recording any agreed protocol differences.
- [ ] Recreate panels (a) and (b), including all five published series and benchmarks.
- [ ] Compare values and trends with the paper and investigate discrepancies.

## Reproduce Table I

- [ ] Implement and validate exponential, deterministic, confirmed Mixed-Erlang,
  and Pareto job-size sampling, with unit mean and separate workload/policy streams.
- [ ] Record all 24 cases and the paper's reference values.
- [ ] Check convergence and uncertainty carefully for heavy-tailed Pareto sizes.
- [ ] Run the cases at 4,000 servers with the reported experiment budget.
- [ ] Compare both metrics against Table I; explain deviations and avoid claiming
  exact insensitivity solely from similar averages.

## Reproduce heterogeneous workloads

- [ ] Add JobClassSettings for class-specific arrival rates, job-size parameters,
  speedups, and maximum parallelism.
- [ ] Add class IDs to workload records and Job instances.
- [ ] Add JobFactory to attach the correct class settings while creating fresh
  jobs from saved inputs; workload generation remains responsible for sampling sizes.
- [ ] Implement class-capacity optimization from (21)-(23) and Algorithm 1;
  validate its output against an independent small optimization calculation.
- [ ] Specify and validate how class fractions become integer server reservations
  in finite systems; document any implementation convention.
- [ ] Apply each class's allocation probabilities within its reserved capacity.
- [ ] Record per-class and overall blocking and execution time.
- [ ] Check reduction to the single-class case, capacity conservation, and small
  multiple-class examples. Label these as validation cases we constructed, since
  the paper does not report a matching multiple-class figure or table.

## Finish reproduction before my own study

- [ ] Complete model documentation and mathematical notes.
- [ ] Link every target to code, checks, settings, saved results, and comparisons.
- [ ] Write a report explaining matches, uncertainty, discrepancies, and limitations.
- [ ] Review the report and unresolved assumptions with Arpan.
- [ ] Save a reproducible baseline revision and commands before making research changes.

## After reproduction: choose the next study

- [ ] Ask Arpan whether a finance application of the model or methods is feasible.
- [ ] Agree the next research question, then update the goal and create a separate
  plan. Finance is one possible direction, not a required outcome.
