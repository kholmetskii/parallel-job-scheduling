# Parallel Job Scheduling

A Python simulation of greedy server allocation for moldable jobs.

## Run

Use Python 3.10 or newer. From the project folder, run:

```bash
.venv/bin/python simulation.py
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
conservation after every event.

## Random workload

Run the M4 example with 100 servers, 1,000 arrivals, and seed 42:

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
arrivals = workload.generate(num_jobs=1000)
result = Simulator(servers=100).run(arrivals)
```

Create a fresh generator with the same seed and settings to reproduce a
workload. Further calls on the same generator continue its random stream;
each generated workload starts its arrival clock at zero. The generator
uses its own random state, leaving Python's global random state untouched.

The example prints arrival, acceptance, rejection, and completion counts.
Warm-up and performance measurements will be added in M5.

## Classes

| Class | Responsibility |
| --- | --- |
| `Job` | Store arrival time and size; set allocation and completion time when started. |
| `ServerPool` | Allocate and release capacity in a pool of identical servers. |
| `Simulator` | Advance time, handle events, check conservation, and record results. |
| `WorkloadGenerator` | Generate ordered arrival times and job sizes using a local random seed. |

`Job`, `ServerPool`, and `Simulator` are in `simulation.py`.
`WorkloadGenerator` is in `workload.py`. To run the fixed example from Python:

```python
from simulation import EXAMPLE_ARRIVALS, Simulator

simulator = Simulator(servers=6)
result = simulator.run(EXAMPLE_ARRIVALS)
```

`run()` accepts ordered `(arrival_time, job_size)` pairs and returns the event
log and counts. Each call starts with an empty system and fresh counters.
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

## Project notes

- [Model](docs/model.md)
- [Plan](docs/plan.md)
