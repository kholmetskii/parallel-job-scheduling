# Paper reproduction checklist

Updated: 17 November 2026.

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

Learning status, 17 November 2026: the student reports no experience with CTMCs,
queueing/loss systems, LP or concavity. The [foundation learning sequence](plan.md#current-focus)
now precedes advanced proof work. Existing checked notes and code retain their
recorded evidence status; they do not establish the student's understanding.

## Coverage and evidence

| Target | Current status | Evidence and work remaining |
| --- | --- | --- |
| Section II: loss-system model | Partial | [Baseline model](model.md), [simulator](../scheduling/simulator.py) and [tests](../tests/test_simulator.py) exist. Immutable [Job](../scheduling/job.py) inputs feed a [ServerPool](../scheduling/server_pool.py) that owns job execution and its private CompletionQueue; Simulator owns time and ordering and uses the two-method `AllocationPolicy` protocol for policy calls (10 November). Statistics owns all counts and measurements, independently of Logger retention (8 November). All 82 tests pass; seeded baseline traces and measurements are preserved for both policies, and disabling event retention preserves every measurement. main.py derives the arrival rate from its configured load, capacity and mean job size; a check with both policies confirms that doubling mean size halves the rate, doubles execution times, and preserves allocations and blocking. [State-accounting notes](model.md#state-variables-normalization-and-steady-state-accounting) explain normalization, state variables, stationary flow balance, Little's law, and the ideal baseline target (17 November). The explanation does not constitute a complete audit of every model assumption. |
| Section III: LP (7), Proposition 1, Theorem 1 | Partial | [Allocation helpers](../scheduling/allocation.py) implement target selection and use equations (8)-(9) to calculate the selected state components and probabilities (9 November). [Twenty allocation tests](../tests/test_allocation.py) cover boundaries, linear/light-load cases, and exact LP vertex checks: target selection for 45 configurations, probability feasibility/optimality for 60 configurations, and all six paper regime/curve combinations at nine server counts (54 cases, checked 9 November). See the [validation evidence](#allocation-validation-9-november-2026). The reusable execution-time benchmark also matches independent LP minima in 234 combinations; see the [benchmark validation](#execution-time-benchmark-validation-9-november-2026). [Allocation-rule notes](model.md#optimal-allocation-calculations) now derive the one/two-neighbour structure, optimal state, arrival probabilities, and benchmark with explicit assumptions (9 November). Exact checks and a question about Theorem 1(ii)'s uniqueness wording are recorded [below](#allocation-rule-derivation-9-november-2026). [Proposition 1](#proposition-1-check-10-november-2026) checked with a scaling qualification (10 November); the policy convergence proof remains pending. |
| Section IV: greedy and greedy(p*) | Partial | main.py uses `RandomizedPolicy.optimal()` to construct the paper's policy from the configured load and speedups (10 November). Tests check configured distributions, single-target cases, changes in load/speedups, event order, and seeded replay. Earlier checks matched six baseline event traces and summaries; the direct main.py run preserves every statistic of the previous randomized baseline. The calculated distributions pass the Section VII regime/curve grid below (9 November); running these settings through the simulator and collecting numerical reproduction evidence remain pending. |
| Section V and Appendices A-E: proof arguments | Partial | The Appendix B allocation structure is explained and independently checked in the [model notes](model.md#optimal-allocation-calculations), 9 November. [Appendix A](#proposition-1-check-10-november-2026) checked for fixed maximum parallelism and a scaling question recorded for growing maximum parallelism. Theorem 2/Section V and the remaining appendices still need detailed assumption and proof checks. Simulations do not establish these results. |
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

main.py calculates `load = normalized_load(SERVERS, ALPHA, BETA)` using a
pure function in that same file. Startup validation checks the configuration,
including the derived load and arrival rate. main() then calculates the load for
its run. Defaults `ALPHA = 0, BETA = 0.2` preserve load 0.8.
For mean inherent job size `m`, main.py uses
`arrival_rate = load * SERVERS / MEAN_JOB_SIZE` and passes that same load to both
allocation helpers. This reduces to the paper's `n * lambda(n)` when `m = 1`,
as in its experiments. Changing server count recalculates load for the chosen
regime; workload generation remains independent of ALPHA/BETA.
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
- [ ] Clarify Theorem 1(ii)'s uniqueness claim under non-strict concavity. The
  [allocation notes](model.md#why-one-target-or-two-neighbouring-targets-suffice)
  give an exact boundary counterexample with speedups `(1, 1.8, 2.6)` and load
  `0.9`. The implemented singleton remains optimal; other optimal states exist.
- [ ] Clarify with Arpan the intended scaling in Proposition 1 and Appendix A.
  The proof controls blocking by the state error times maximum speedup, divided
  by load. The [two-state example](theory.md) satisfies the unweighted error
  condition but has constant blocking when `d(n) = n`.
- [ ] Check Section VI's job-size/service-rate notation and Algorithm 1's capacity
  update against optimization problems (21)-(23) before translating them into code.
- [ ] Agree documented assumptions for unreported details if original information
  cannot be recovered, and label the resulting reproduction accordingly.

These questions do not prevent work on the general single-class implementation.
Record answers and their source here when received; do not invent missing settings.

## Generalize the single-class implementation

- [x] Derive arrival rate from normalized load, server count, and mean job size.
  Completed 8 November 2026; the formula is now directly in main.py (9 November).
- [x] Calculate normalized load from server count and ALPHA/BETA in main.py.
  Completed 9 November 2026 at the user's request; keep the pure helper next to
  configuration. Startup validation checks parameters and the derived load once.
  tests/test_main.py checks known values for all three regimes and verifies that
  main.py supplies the changed load to workload and allocation calculations.
  All 79 tests pass; the complete default main.py output is unchanged.
- [x] Find the optimal single target or two adjacent targets in `scheduling/allocation.py`.
  Completed 9 November 2026; target selection matches exact LP minima in 45 cases.
- [x] Calculate their probabilities from the model settings.
  Completed 9 November 2026; feasibility and LP optimality checked in 60 cases.
- [x] Make RandomizedPolicy use the calculated targets and probabilities.
  Completed 9 November 2026; model changes determine the experiment's distribution.
  On 10 November, move setup into `RandomizedPolicy.optimal()` and keep the
  explicit constructor. [The main integration test](../tests/test_main.py)
  checks the resulting targets and weights at load 0.995. All 82 tests pass;
  the default seeded output, including the theoretical benchmark, is identical.
- [x] Validate the allocation rule for all three Section VII traffic regimes and
  both speedup curves. Completed 9 November 2026; 54 cases pass the independent
  checks recorded below. This validates allocations, not the published simulations.
- [x] Calculate the theoretical mean execution-time benchmark.
  Completed 9 November 2026; allocation.py returns the LP objective in configured
  mean-size units, and main.py prints it alongside the measured mean. The checks
  below cover independent LP optimality, single targets, linear speedups and scaling.
- [x] Check the known case: targets 3/4, probabilities 0.625/0.375, benchmark 0.375.
  Completed 9 November 2026; regression tests and the worked example in model.md
  match Section VII's unit-mean result. The printed default benchmark is 0.375000.
- [x] Test single-target cases, boundary loads, linear speedups, and invalid inputs.
  Completed 9 November 2026; allocation, policy, and experiment tests pass.
- [x] Recheck the 100-server baseline after generalizing the policy; earlier saved outputs have been removed.
  Completed 9 November 2026; six event traces/summaries and main.py output match
  the implementation immediately before policy integration. New published-result
  reproduction evidence remains pending.

### Allocation validation: 9 November 2026

Source checked against the paper: Section III, LP (7) and Theorem 1 on printed
page 387 (PDF page 4); the probability conversion in Section IV on the same page;
and Section VII's traffic parameters and two speedup curves on printed page 392
(PDF page 9). Table I on printed page 393 specifies `n = 4000`.

The regression test
`AllocationProbabilitiesTests.test_paper_traffic_regimes_and_speedup_curves` in
[tests/test_allocation.py](../tests/test_allocation.py) calculates
`lambda(n) = 1 - beta * n**(-alpha)` for all six regime/curve combinations and
`n = 1, 25, 50, 100, 200, 500, 1000, 4000, 10000` (54 cases). These are our chosen
validation points; the exact Figure 2 points remain unresolved. The `n = 1` case
checks the sublinear efficiency boundary at load 0.9.

Each case checks the expected target support, finite nonnegative probabilities
summing to one, and server-capacity feasibility. Its objective value
`sum(p_i / s_i)` is compared to the minimum from the existing independent exact
LP vertex enumeration, including all single-target and all two-target supports,
not just neighbouring pairs. Decimalized floating-point loads are passed to that
oracle as Fractions; objectives agree to 12 decimal places.

Calculated allocations at `n = 4000` (probabilities rounded to nine decimal places):

| Regime | Speedups | Normalized load | Targets | Probabilities in target order |
| --- | --- | ---: | --- | --- |
| Mean-field | Linear | 0.800000000 | 5 | 1 |
| Halfin-Whitt | Linear | 0.998418861 | 5 | 1 |
| Super-Halfin-Whitt | Linear | 0.999603150 | 5 | 1 |
| Mean-field | Sublinear | 0.800000000 | 3, 4 | 0.625, 0.375 |
| Halfin-Whitt | Sublinear | 0.998418861 | 1, 2 | 0.985747215, 0.014252785 |
| Super-Halfin-Whitt | Sublinear | 0.999603150 | 1, 2 | 0.996426930, 0.003573070 |

Run the allocation checks and the complete suite from the project directory:

```bash
.venv/bin/python -B -m unittest discover -s tests -p test_allocation.py -v
.venv/bin/python -B -m unittest discover -s tests -q
```

Outcome: all 17 allocation tests and all 78 project tests pass. No allocation
implementation change was needed. This is a finite grid check of the analytical
rule, not a proof for every input or a reproduction of Figure 2/Table I metrics.
This allocation-only check did not yet cover the reusable benchmark; its
subsequent validation is recorded below. Proof notes and paper simulation evidence
remain open tasks. The simulator and main.py's run settings are unchanged.

### Execution-time benchmark validation: 9 November 2026

[optimal_mean_execution_time()](../scheduling/allocation.py) returns
`mean_job_size * sum(p_i / s_i)` using the existing optimal targets and
probabilities. Section III's LP (7), printed page 387 (PDF page 4), minimizes
`sum(y_i) / load` for unit mean size. Section IV defines `p_i = s_i * y_i / load`,
so substituting gives `sum(p_i / s_i)`. Our configured mean size scales execution
times by that mean; it does not change the optimal probabilities at fixed load.
Section VII, printed pages 392-393 (PDF pages 9-10), supplies the reference values
0.2 for linear speedups and 0.375 for the sublinear mean-field case.
The [model notes](model.md#optimal-allocation-calculations) give a worked example.

[tests/test_allocation.py](../tests/test_allocation.py) checks:

- The known unit-mean baseline of 0.375; linear, single-server, light-load and
  efficiency-boundary cases; and three independently specified mean-size examples.
- Agreement to 12 decimal places with the independent exact LP vertex minimum
  for five speedup curves and twelve loads at mean sizes 0.5, 1 and 2.5
  (180 benchmark combinations).
- Agreement with the LP minimum at unit mean size for the earlier 54-case paper
  traffic-regime/speedup grid, including `n = 4000`.

[tests/test_main.py](../tests/test_main.py) checks the complete main() flow with
400 servers, `ALPHA = 1 / 2`, `BETA = 0.1`, and mean size 2. The arrival rate is
199; at load 0.995 the policy targets one and two servers with respective
probabilities 190/199 and 9/199; and the benchmark prints as 1.959799. This catches mismatched load or time units at the entry point.

Validation commands from the project directory:

```bash
.venv/bin/python -B -m unittest discover -s tests -q
.venv/bin/python -B main.py
```

Outcome: all 20 allocation tests and all 82 project tests pass. The full previous
default output is preserved, with one new line:

```text
Blocking probability: 0.119190
Mean execution time: 0.395893
Theoretical mean execution-time benchmark: 0.375000
```

The first two lines are the existing finite 100-server simulation, not new paper
reproduction estimates. The benchmark is the LP/asymptotic reference; a finite
system can differ because of capacity limits and sampling variability. This check
does not establish convergence, numerical reproduction, or the paper's proofs.

## Allocation-rule derivation: 9 November 2026

**Status: allocation explanation complete; stochastic convergence not verified.**
The [model notes](model.md#optimal-allocation-calculations) now explain the
single-class LP, why a vertex has at most two positive components, and why
concavity permits adjacent targets. A supporting-line inequality proves the
selected state's global optimality. The notes derive equations (8)-(9),
`p_i* = s_i * y_i* / load`, and `D* = mean_job_size * sum(p_i* / s_i)`.

At the user's request, the same notes were then organized as local Definition
A1; Lemmas A1-A3; Propositions A1-A3; Theorem A1; and Corollaries A1-A2, each
claimed result accompanied by a proof. Lemma A2 proves the sparse-optimum
property by an explicit support-reducing perturbation; Lemma A3 supplies the
supporting-line certificate used in the target-selection theorem. Both
counterexamples include exact feasibility and objective calculations. These
labels belong to our explanatory notes, not the paper. In particular, local
Proposition A1 does not verify the paper's Proposition 1. Exact rational
checks of the formal formulas match independent LP minima for 99 load/curve
cases, and both counterexamples' objectives and feasibility are verified.

The finished Obsidian-format notes are saved in [theory.md](theory.md),
created 9 November 2026 from the version supplied in chat.
Formatting repaired on the same date: blank lines around display equations
and LaTeX comparison commands avoid accidental HTML parsing in Markdown
previews. The statements, formulas, and all nine proofs are preserved.

Sources checked: Section II's P1-P2 on printed page 386 (PDF page 3); Section
III's LP (7) and Theorem 1, equations (8)-(10), and Section IV's probability
conversion on page 387 (PDF page 4); and Appendix B on pages 393-395 (PDF pages
10-12). The supporting-line presentation is our explanatory derivation of the
LP's solution rather than a reproduction of every KKT step in Appendix B.

Assumptions are explicit: one shared increasing speedup curve, discrete
concavity including `s_0 = 0`, `s_1 = 1`, finite positive mean job size, and
`0 < load < 1` in the implementation. Theorem 1 also permits unit load; zero
load makes the formulas undefined and load above one makes the LP infeasible.
The Poisson/exponential stochastic model is distinguished from the deterministic
optimization. Target probabilities are distinguished from actual finite-system
allocations, which are capped by idle capacity.

Verification used exact rational arithmetic for the baseline state, probabilities,
benchmark, single-target/boundary and linear cases, 14 supporting-line
inequalities and 31 feasible optimal states, the nonconcave skipped-target
example, and the following nonuniqueness example. The existing 82-test suite also
passes with `.venv/bin/python -B -m unittest discover -s tests -q`. This is
explanation/validation evidence, not a published numerical reproduction run.

**Unresolved source wording:** Theorem 1(ii) calls its boundary solution unique
under P1-P2. With the valid increasing concave curve `(1, 1.8, 2.6)` and load
`0.9 = s_2 / 2`, both `(0, 0.5, 0)` and `(0.25, 0, 0.25)` satisfy throughput
`0.9` and occupancy `1` and attain the certified minimum objective `5/9` for
unit mean size. Thus our notes state existence of an optimal singleton here,
without claiming unconditional uniqueness. The implemented choice `(2,)`
remains correct. Clarification with Arpan is pending; no supervisor resolution
is implied.

## Proposition 1 check: 10 November 2026

Checked Proposition 1 (printed p. 387, PDF p. 4) and Appendix A (printed
p. 393, PDF p. 10) against equations (3)-(4). The [theory notes](theory.md)
derive the finite-system bounds from rate conservation and Little's law.
The sufficient condition follows for bounded `d(n)` and load bounded away
from zero, including the paper's fixed `d = 5` experiment settings. More
generally it follows when `max_speedup * mean_state_error / load` tends to
zero. This is an implication conditional on state convergence, not a proof
that the policy attains it.

The broader wording leaves the maximum-speedup factor implicit. For linear
speedups, `d(n) = n`, and load `4/5`, allocating all servers to each accepted
job yields a two-state chain. Exact rate balance gives blocking `4/9` and
mean normalized state error `8/(15*n)`. This meets the unweighted criterion
but retains positive blocking. The example falls outside Theorem 2's
`d(n) = o(n)` assumption; that theorem's conditions and proof remain to be
checked. No simulation or code change was needed for this check.

## Check the mathematical results

- [x] Explain the normalization, state variables, flow conservation, and Little's law
  in Section II and equations (3)-(7). Completed 17 November 2026; see the
  [state-accounting notes](model.md#state-variables-normalization-and-steady-state-accounting),
  checked against printed pp. 385-387. Exact arithmetic verifies the baseline
  target constraints and benchmark. This records an explanation, not assessed
  student understanding or completion of the stochastic convergence proof.
- [x] Derive Theorem 1's one/two-neighbour allocation choices and verify feasible
  states and objective values independently. Completed 9 November 2026; see the
  [allocation-rule derivation](#allocation-rule-derivation-9-november-2026).
  Record the weak-concavity uniqueness issue as unresolved source wording.
- [x] Check the conversion from optimal state y* to arrival probabilities p* and D*.
  Completed 9 November 2026; the notes derive it from allocation-specific Little's
  law, with normalization and mean-size scaling checked exactly.
- [x] Check Proposition 1's sufficient condition for asymptotic optimality and
  its assumptions. Completed 10 November 2026; see the
  [Appendix A review](#proposition-1-check-10-november-2026) and the open scaling question above.
- [ ] Write out the finite-state transition rates and generator used in Section V.
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
