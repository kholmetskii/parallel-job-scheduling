# Model

We simulate jobs sharing a pool of servers. We compare greedy allocation
with the paper's randomized rule to study blocking and execution time.

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

## Randomized allocation

- For the current rate `0.8 * n`, mean size 1, and speedups below, target 3
  servers with probability `0.625` and 4 with probability `0.375`.
- Allocate `min(target, idle servers)`. Reject only when none is idle.
- Use a separate seeded random generator for allocation decisions. Sample a
  target for every arrival, including warm-up and rejected arrivals.
- Keep the allocation fixed until completion. Recalculate the probabilities
  if the normalized load or speedup function changes.

## Execution and completion

- Speedups for 1, 2, 3, 4, and 5 servers are `1, 1.8, 2.5, 3, 3.4`, respectively.
- Execution time is `job size / speedup`.
- On completion, release all of the job's servers together.
- Process completions before arrivals at the same time. Process simultaneous
  arrivals in input order.

## Measurements

- **Blocking probability:** rejected arrivals divided by total arrivals.
- **Mean execution time:** average full execution time of accepted jobs.
- Process a configurable number of initial arrivals as warm-up, counting both
  accepted and rejected arrivals toward the cutoff. Keep running jobs and
  their allocations when warm-up ends.
- Measure subsequent arrivals. Exclude warm-up jobs even if they finish later.
  Include the full execution time of measured accepted jobs that finish after
  the final arrival. Choose experimental warm-up and run lengths in M6.
- If there are no measured arrivals, blocking probability is unavailable.
- If no measured job is accepted, mean execution time is unavailable.

## Reference

Mukhopadhyay, A., Ghanbarian, S., Mazumdar, R. R. and Guillemin, F. (2026).
*On Optimal Server Allocation for a Loss System With Moldable Jobs*.
IEEE Transactions on Networking, 34. Sections II, IV, and VII.
[Paper DOI](https://doi.org/10.1109/TON.2025.3598595).
