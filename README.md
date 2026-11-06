# Parallel Job Scheduling

A Python simulation comparing greedy and randomized server allocation for moldable jobs.

## Run

Use Python 3.10 or newer. From the project folder, run:

```bash
.venv/bin/python run_fixed.py
```

This runs the M3 hand-worked example with 6 servers and fixed inputs:

| Arrival time | Job size |
| --- | --- |
| 0.0 | 3.4 |
| 0.2 | 1.0 |
| 0.4 | 1.0 |
| 1.0 | 3.4 |

Expected event log:

| Time | Event | Idle servers afterward |
| --- | --- | --- |
| 0.0 | Job 1 receives 5 servers | 1 |
| 0.2 | Job 2 receives 1 server | 0 |
| 0.4 | Job 3 is rejected | 0 |
| 1.0 | Job 1 completes | 5 |
| 1.0 | Job 4 receives 5 servers | 0 |
| 1.2 | Job 2 completes | 1 |
| 2.0 | Job 4 completes | 6 |

The final counts are 3 accepted jobs, 1 rejected job, and 3 completions.
All 6 servers are idle at the end. The simulator checks server and job
conservation after every event. With no warm-up, blocking probability is
`1 / 4 = 0.25` and mean execution time is `1.0`.

Both runners use the same summary labels and order for whole-run counts,
warm-up, measured counts, and metrics. Metrics use six decimal places, or
`unavailable` when there are no observations. The fixed runner also prints
the detailed event log.

## Random workload

Run the example with 100 servers, 11,000 arrivals, and seed 42. The first
1,000 arrivals are warm-up; the following 10,000 are measured:

```bash
.venv/bin/python run_random.py
```

This example uses the greedy allocation policy with a randomly generated workload.

The generator uses exponential gaps with rate `0.8 * servers` to produce
Poisson arrivals. Job sizes are sampled independently from an exponential
distribution with mean 1. The first arrival follows a random gap from time zero.

To choose the settings from Python:

```python
from simulation import Simulator
from workload import WorkloadGenerator

workload = WorkloadGenerator(arrival_rate=80, mean_job_size=1, seed=42)
arrivals = workload.generate(num_jobs=11_000)
result = Simulator(servers=100).run(arrivals, warmup_arrivals=1_000)
```

Create a fresh generator with the same seed and settings to reproduce a
workload. Further calls on the same generator continue its random stream;
each generated workload starts its arrival clock at zero. The generator
uses its own random state, leaving Python's global random state untouched.

The example prints counts for the whole run, the warm-up cutoff, measured
counts, blocking probability, and mean execution time. These are demonstration
settings. The M6 experiment checks longer warm-up and measurement settings.

## Experiment

Run the 100-server greedy baseline and sensitivity checks:

```bash
.venv/bin/python run_experiment.py
```

The script runs six configurations with seeds 0–9, for 60 runs in total.
It compares warm-up counts of 1,000, 5,000, and 10,000 at 100,000 measured
arrivals, and measured run lengths of 10,000, 50,000, 100,000, and 200,000
at a fixed 10,000-arrival warm-up. Every run uses a fresh simulator and
workload generator, and keeps conservation checks enabled.

- [Experiment report](docs/experiment_results.md): settings, means and sample
  standard deviations across seeds, paired sensitivity comparisons, and
  baseline results for each seed.
- [Complete results](results/greedy_experiment.json): one record per run,
  aggregate results, comparison tolerances, Python version, and source hashes.

The script regenerates these two files. Configurations sharing a seed reuse
the same workload prefix; comparisons therefore pair matching seeds. The
report distinguishes observed stability from proof of steady-state operation.

The [results figure](results/figures/greedy_sensitivity.png) compares both
metrics across warm-up and measured run lengths. Points show configuration
means; error bars show one sample standard deviation across seeds. The
selected baseline is highlighted. An [SVG version](results/figures/greedy_sensitivity.svg)
is available for scalable figures in the report.

To regenerate the figure from the saved results, use Python 3.11 or newer:

```bash
.venv/bin/python -m pip install -r requirements-plot.txt
.venv/bin/python plot_results.py
```

Plotting is optional; the simulator and experiment runner use the standard
library. Regenerate the figure after running a new experiment.

## Policy comparison

Run the M7 comparison with matching workloads for both policies:

```bash
.venv/bin/python run_comparison.py
```

`GreedyPolicy` targets 5 servers. `RandomizedPolicy` implements the paper's
`greedy(p*)` rule for the current model: target 3 with probability 0.625 and
4 with probability 0.375, then cap the allocation by idle capacity. These
probabilities apply to normalized arrival rate 0.8, mean size 1, and the
current speedups; they must be recalculated if these parameters change.

The experiment runs both policies on the same arrivals and sizes for ten
workload seeds. It uses a separate allocation generator with seed
`10000 + workload_seed` and samples one target per arrival, including warm-up
and blocked arrivals. Both policies use 10,000 warm-up and 100,000 measured
arrivals. The randomized policy also receives the six sensitivity configurations
from M6, giving 70 runs in total. Shared input hashes are checked before
calculating paired differences.

- [Comparison report](docs/policy_comparison.md): both metrics, paired policy
  differences, randomized sensitivity checks, and interpretation at 100 servers.
- [Complete comparison results](results/policy_comparison.json): every run,
  both seeds, actual allocation counts, workload hashes, summaries, and embedded
  source text and fingerprints.
- [Comparison figure](results/figures/policy_comparison.png), with an
  [SVG version](results/figures/policy_comparison.svg) for the report.

Regenerate the figure after a comparison run, using the optional plotting
dependency described above:

```bash
.venv/bin/python plot_comparison.py
```

To select the randomized policy directly:

```python
from policies import RandomizedPolicy

result = Simulator(servers=100, policy=RandomizedPolicy(seed=10042)).run(
    arrivals, warmup_arrivals=1000,
)
```

Omitting `policy` selects greedy. Every simulator run resets the policy's
random stream, so a fixed policy seed and workload reproduce the same result.
The [original M6 source snapshot](results/greedy_source.json) preserves the
files matching the historical greedy experiment's hashes. Future M6 runs
regenerate that snapshot together with their results.

## Randomized policy across server counts

Compare 25, 50, 100, 200, 500, and 1,000 servers:

```bash
.venv/bin/python run_server_experiment.py
```

Arrival rate scales as `0.8 * servers`, keeping offered load per server at
0.8 instead of making larger systems less loaded. Mean job size, speedups,
and randomized target probabilities stay fixed. Each size uses seeds 0–9,
10,000 warm-up and 100,000 measured arrivals, giving 60 runs. Matching
workload and policy seeds share random draws across sizes; arrival times
scale with arrival rate.

- [Server-count report](docs/server_experiment.md): settings, results and limitations.
- [Complete results](results/randomized_servers.json): individual runs and source snapshots.
- [Figure](results/figures/randomized_servers.png), with an
  [SVG version](results/figures/randomized_servers.svg) for the report.

Regenerate the figure with the optional plotting dependency:

```bash
.venv/bin/python plot_server_experiment.py
```

The 100-server settings are reused for this exploratory comparison; warm-up
and run length have not been separately validated for every system size.

## Measurements

`run()` accepts `warmup_arrivals=0` by default. The first `warmup_arrivals`
input jobs are processed normally but excluded from statistics, whether
accepted or rejected. Running jobs keep their servers across the cutoff.
Jobs are selected for measurement by arrival number, including when arrivals
share a timestamp.

Top-level result counts and the event log cover the whole run. The
`result["statistics"]` dictionary contains the configured warm-up count,
measured arrival, acceptance, and rejection counts, total execution time,
and these metrics:

| Metric | Calculation |
| --- | --- |
| `blocking_probability` | Measured rejections / measured arrivals. |
| `mean_execution_time` | Total full execution time / measured accepted jobs. |

Execution time is `completion_time - arrival_time`. Its full value is known
when a job starts, so statistics accumulate it at acceptance. Measured jobs
that finish after the last arrival contribute their full duration. Warm-up
jobs contribute no duration, including when they complete after the cutoff.

With no measured arrivals, both metrics are `None`. With measured arrivals
but no accepted jobs, blocking probability is `1.0` and mean execution time
is `None`. A cutoff equal to or greater than the input length produces no
measured arrivals.

## Classes

| Class | Responsibility |
| --- | --- |
| `Job` | Store arrival time and size; set allocation and completion time when started. |
| `ServerPool` | Allocate and release capacity in a pool of identical servers. |
| `Statistics` | Count measured admissions and accumulate full execution times after warm-up. |
| `Simulator` | Advance time, handle events, check conservation, and record results. |
| `WorkloadGenerator` | Generate ordered arrival times and job sizes using a local random seed. |
| `GreedyPolicy` | Select as many idle servers as possible, up to the maximum. |
| `RandomizedPolicy` | Sample a target of 3 or 4 and cap it by idle capacity. |

`Job`, `ServerPool`, `Statistics`, and `Simulator` are in `simulation.py`.
`WorkloadGenerator` is in `workload.py`; allocation policies are in `policies.py`.
To run the fixed example from Python:

```python
from run_fixed import EXAMPLE_ARRIVALS
from simulation import Simulator

simulator = Simulator(servers=6)
result = simulator.run(EXAMPLE_ARRIVALS)
```

`run()` accepts ordered `(arrival_time, job_size)` pairs and returns the event
log, whole-run counts, and statistics. Each call starts with an empty system
and fresh counters and statistics.
The example uses 6 servers to make each event easy to check; the initial
research model uses 100.

## Check

```bash
.venv/bin/python -m unittest -v
```

Checks cover the expected trace, simultaneous events, partial allocation,
blocking, empty input, invalid inputs, job allocations, pool capacity, and
fresh state between runs. Workload checks cover seeded reproducibility,
ordered arrivals, valid sizes and settings, distribution sanity, and
integration with the simulator.
Measurement checks cover known metrics, warm-up boundaries and retained
allocations, late completions, empty measurements, zero-duration jobs,
resetting statistics, and an independent calculation from the event log.
Experiment checks cover trial counts, sample standard deviations, duplicate
seeds, and matching seeds correctly in paired comparisons.
Policy checks cover target probabilities, partial allocation, blocked draws,
local randomness, seeded replay, and unchanged greedy behavior. Comparison
checks enforce matching inputs and verify paired differences against known values.

## Project notes

- [Model](docs/model.md)
- [Plan](docs/plan.md)
