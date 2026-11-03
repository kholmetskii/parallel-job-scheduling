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

`simulate(arrivals, servers=100)` accepts ordered `(arrival_time, job_size)`
pairs and returns the event log and counts. The example uses 6 servers to make
each event easy to check; the initial research model uses 100.

## Check

```bash
.venv/bin/python -m unittest -v
```

Checks cover the expected trace, simultaneous events, partial allocation,
blocking, empty input, and invalid inputs. Random arrivals and sizes come in M4.

## Project notes

- [Model](docs/model.md)
- [Plan](docs/plan.md)
