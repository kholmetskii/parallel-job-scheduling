# Model

We simulate jobs sharing a pool of servers. The first version uses greedy
allocation to study blocking and execution time.

## Servers

- Start with 100 identical servers, all idle.
- Each server can work on one job at a time.
- Each job can use up to 5 servers together.

## Jobs and arrivals

- Jobs arrive according to a Poisson process at rate `0.8 * n`, where `n` is
  the number of servers. With 100 servers, this averages 80 arrivals per time unit.
- Each job has an exponential size `X` with mean 1. This is its execution time
  on one server.
- Job sizes are independent of each other and of arrivals.
- Time is measured in units where average one-server execution time is 1.

## Greedy allocation

- When a job arrives, give it `min(5, idle servers)` servers.
- If no server is idle, reject the job. There is no waiting queue or retry.
- An accepted job starts immediately and keeps its allocation until completion.

## Execution and completion

- Speedups for 1, 2, 3, 4, and 5 servers are `1, 1.8, 2.5, 3, 3.4`, respectively.
- Execution time is `job size / speedup`.
- On completion, release all of the job's servers together.
- Process completions before arrivals at the same time. Process simultaneous
  arrivals in input order.

## Measurements

- **Blocking probability:** rejected arrivals divided by total arrivals.
- **Mean execution time:** average full execution time of accepted jobs.
- Measure arrivals after an initial warm-up. Include accepted jobs that finish
  after measured arrivals stop. Choose warm-up and run lengths in M5-M6.
- If no measured job is accepted, mean execution time is unavailable.

## Reference

Mukhopadhyay, A., Ghanbarian, S., Mazumdar, R. R. and Guillemin, F. (2026).
*On Optimal Server Allocation for a Loss System With Moldable Jobs*.
IEEE Transactions on Networking, 34. Sections II, IV, and VII.
[Paper DOI](https://doi.org/10.1109/TON.2025.3598595).
