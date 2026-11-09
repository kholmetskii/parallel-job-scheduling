# Model

We simulate jobs sharing a pool of servers to study blocking and execution time.
The simulator supports greedy allocation and the paper's randomized rule;
main.py currently runs the randomized rule once.

The settings below describe the baseline experiments. The simulator also accepts
a configured speedup curve; its length determines the maximum allocation.

## Servers

- Start with 100 identical servers, all idle.
- Each server can work on one job at a time.
- In the baseline, each job can use up to 5 servers together.

## Jobs and arrivals

- Jobs arrive according to a Poisson process at rate `0.8 * n`, where `n` is
  the number of servers. With 100 servers, this averages 80 arrivals per time unit.
- main.py derives the general rate as
  `NORMALIZED_LOAD * SERVERS / MEAN_JOB_SIZE`. Workload generation uses this
  property, so changing mean size preserves the configured load.
- Each job has an exponential size `X` with mean 1. This is its execution time
  on one server.
- Job sizes are independent of each other and of arrivals.
- Time is measured in units where average one-server execution time is 1.
- Workloads contain immutable `Job(id, size, arrival_time)` objects, which can
  be shared between policy runs. IDs must be unique within each workload.

## Greedy allocation

- When a job arrives, give it `min(maximum allocation, idle servers)` servers.
  The default maximum is the number of speedup entries, which is 5 in the baseline.
- If no server is idle, reject the job. There is no waiting queue or retry.
- An accepted job starts immediately and keeps its allocation until completion.

## Randomized allocation

- For the current rate `0.8 * n`, mean size 1, and speedups below, target 3
  servers with probability `0.625` and 4 with probability `0.375`.
- main.py calculates targets and probabilities from its configured load and speedups and passes them to
  `RandomizedPolicy(targets, probabilities, seed=...)`. The policy stores the
  distribution and samples it; the mathematical calculations stay in allocation.py.
- Allocate `min(target, idle servers)`. Reject only when none is idle.
- Use a separate seeded random generator for allocation decisions. Sample a
  target for every arrival, including warm-up and rejected arrivals.
- Keep the allocation fixed until completion. Changing normalized load or speedups
  recalculates the distribution when main.py constructs its policy.

## Optimal allocation calculations

`optimal_allocation_targets(normalized_load, speedups)` in
`scheduling/allocation.py` implements the target selection in Theorem 1:

- Let `s_i / i` be the efficiency of an allocation of `i` servers.
- At or below the maximum allocation's efficiency, return that maximum alone.
- At an efficiency boundary, return the largest matching allocation alone.
- Between two neighbouring efficiencies, return their two allocation sizes.

The function returns an increasing tuple, such as `(3, 4)` for the baseline.
It validates its load and speedup inputs and has no random state. A tolerance of four
floating-point steps handles division rounding at boundaries below unit load.
Loads slightly below 1 still select a pair when required by a sublinear curve.

`optimal_allocation_probabilities(normalized_load, speedups)` returns probabilities
in the same order as the targets. A single target has probability `(1.0,)`.
For a neighbouring pair, it calculates the optimal state values `y_i` using
Theorem 1, equations (8)-(9), then applies `p_i = s_i * y_i / normalized_load`
from Section IV. Here `y_i` is the expected number of jobs using `i` servers,
divided by the total server count. The probabilities are normalized to absorb
floating-point round-off. For the baseline they are approximately `(0.625, 0.375)`.
These calculations configure RandomizedPolicy directly in main.py.
Direct policy construction requires explicit targets and probabilities. Targets
are unique positive integers; probabilities are finite, nonnegative, and sum to 1
within rounding tolerance. The policy copies both input sequences into tuples.

## Execution and completion

- main.py holds the run configuration. Simulator and ServerPool receive server
  count and speedups explicitly; reusable modules do not import the entry point.
- Speedups for 1, 2, 3, 4, and 5 servers are `1, 1.8, 2.5, 3, 3.4`, respectively.
- Execution time is `job size / speedup`.
- ServerPool calculates completion time using the chosen allocation's speedup.
  Starting a job reserves capacity and schedules its completion together;
  completing a job removes that completion and releases its allocation together.
- ServerPool owns a private CompletionQueue with entries
  `(completion_time, job_id, allocated_servers, job)`. Allocation and completion
  time belong to that run rather than the input job. Simulator advances time
  and coordinates arrivals, completions, Statistics, and Logger.
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
- Statistics owns whole-run counts and measurements after warm-up, including
  allocation frequencies. Logger records optional event history independently;
  `record_events=False` leaves all measurements unchanged.

## Reference

Mukhopadhyay, A., Ghanbarian, S., Mazumdar, R. R. and Guillemin, F. (2026).
*On Optimal Server Allocation for a Loss System With Moldable Jobs*.
IEEE Transactions on Networking, 34. Sections II, IV, and VII.
[Paper DOI](https://doi.org/10.1109/TON.2025.3598595).
