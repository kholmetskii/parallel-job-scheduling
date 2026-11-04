# Parallel Job Scheduling

A Python simulation of greedy server allocation for moldable jobs.

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
settings; warm-up and run lengths for the experiment will be checked in M6.

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

`Job`, `ServerPool`, `Statistics`, and `Simulator` are in `simulation.py`.
`WorkloadGenerator` is in `workload.py`. To run the fixed example from Python:

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

## Project notes

- [Model](docs/model.md)
- [Plan](docs/plan.md)
