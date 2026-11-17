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
- main.py holds `SERVERS`, `ALPHA`, and `BETA`. Its pure function
  `normalized_load(servers, alpha, beta)` calculates
  `load = 1 - beta * servers ** (-alpha)`. Defaults `ALPHA = 0` and `BETA = 0.2`
  retain load 0.8. Halfin-Whitt uses `ALPHA = 1 / 2, BETA = 0.1`;
  super-Halfin-Whitt uses `ALPHA = 2 / 3, BETA = 0.1`.
- Startup validation checks the configuration, including the derived load and
  arrival rate. main() then calculates the load for its allocation calculations
  and the arrival rate
  `load * SERVERS / MEAN_JOB_SIZE`. Changing mean size preserves that load;
  changing server count recalculates it from the chosen traffic parameters.
  WorkloadGenerator receives only the arrival rate and mean size.
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
- main.py constructs `RandomizedPolicy.optimal(load, SPEEDUPS, seed=...)`.
  The named constructor derives the target distribution using allocation.py.
  The regular constructor also accepts explicit targets and probabilities.
- Allocate `min(target, idle servers)`. Reject only when none is idle.
- Use a separate seeded random generator for allocation decisions. Sample a
  target for every arrival, including warm-up and rejected arrivals.
- Keep the allocation fixed until completion. Changing normalized load or speedups
  recalculates the distribution when main.py constructs its policy.

## State variables, normalization, and steady-state accounting

Checked 17 November 2026 against Section II and Section III, equations (3)-(7),
of Mukhopadhyay et al., *On Optimal Server Allocation for a Loss System With
Moldable Jobs*, printed pages 385-387 (PDF pages 2-4). The following explanation
uses independent exponential inherent job sizes with mean one, as in the paper
and the current default configuration. It does not establish the student's
understanding or verify Theorem 2.

### Arrival normalization and state variables

Fix `n` servers and maximum allocation `d`, suppressing the paper's superscript
`(n)`, which labels the system size rather than a power. The total Poisson arrival
intensity is `a = n * lambda(n)`, where

$$
\lambda(n)=1-\beta n^{-\alpha}.
$$

For the current `alpha = 0`, `beta = 0.2`, and `n = 100`, this gives `lambda = 0.8`
and 80 arrivals per time unit. Scaling arrivals with `n` allows comparison of
different system sizes at a specified offered load per server. This offered load
measures incoming one-server work; actual utilization depends on allocation and
blocking.

Let `X_i(t)` be the number of running jobs allocated exactly `i` servers. Define
`x_i(t) = X_i(t) / n`. Then

$$
N(t)=\sum_{i=1}^d X_i(t),\qquad
q_1(t)=\sum_{i=1}^d i x_i(t),\qquad q_0(t)=1-q_1(t).
$$

Here `N(t)` counts jobs, `q_1(t)` is the busy-server fraction, and `q_0(t)` is
the idle-server fraction. Capacity requires `sum_i i*x_i(t) <= 1` at every time.
The components `x_i` are jobs per server, not an arrival probability distribution.
For example, 20 jobs each using three servers give `x_3 = 0.2`, 20 running jobs,
and 60 occupied servers, hence `q_1 = 0.6`.

### Flow conservation

In stationarity, the distribution remains unchanged while individual job counts
continue to fluctuate. Write `x_i` for a state sampled from that distribution,
and let `P_b` be the blocking probability seen by arrivals. The accepted arrival
rate is `n*lambda*(1-P_b)`.

A job using `i` servers has exponential execution time `X/s_i`, with mean `1/s_i`
and completion rate `s_i`. Therefore the instantaneous total completion intensity
is `sum_i s_i*X_i(t)`. Its stationary average must equal the accepted arrival rate:

$$
n\lambda(1-P_b)=\sum_i s_i\mathbb E[X_i].
$$

Dividing by `n` gives the paper's equation (3):

$$
\lambda(1-P_b)=\sum_i s_i\mathbb E[x_i]=\mathbb E[r(x)],
\qquad r(x):=\sum_i s_i x_i.
$$

The equality holds for stationary averages, not for every instantaneous state.
It is job flow conservation: every admitted job eventually completes. The weights
`s_i` describe completions, whereas the weights `i` describe occupied servers.

### Little's law and execution time

Little's law states `L = a_eff * W`, where `L` is the mean number of jobs present,
`a_eff` is the admitted arrival rate, and `W` is their mean time in the system.
Here accepted jobs start immediately, so their time in the system is execution
time. Rejected jobs never enter. Thus

$$
L=\sum_i\mathbb E[X_i],\qquad
a_{\mathrm{eff}}=n\lambda(1-P_b),\qquad W=\mathbb E[D].
$$

Substitution and division by `n` give equation (4):

$$
\lambda(1-P_b)\mathbb E[D]=\sum_i\mathbb E[x_i],
\qquad
\mathbb E[D]=\frac{\sum_i\mathbb E[x_i]}{\lambda(1-P_b)}.
$$

Use stationary mean job counts in this formula, rather than a single snapshot.
The accepted arrival rate belongs in the denominator because the population in
`L` consists of accepted jobs.

### Worked ideal target for the current baseline

The zero-blocking LP uses deterministic target values `y_i` in place of
`E[x_i]`. For `lambda = 0.8`, `s_3 = 2.5`, and `s_4 = 3`, the selected optimum is
`y_3 = 0.2`, `y_4 = 0.1`, and all other components zero. Check both constraints:

$$
\sum_i i y_i=3(0.2)+4(0.1)=1,\qquad
\sum_i s_i y_i=2.5(0.2)+3(0.1)=0.8.
$$

Its mean execution-time objective is

$$
D^*=\frac{0.2+0.1}{0.8}=0.375.
$$

For `n = 100`, those targets correspond to 30 jobs and 100 occupied servers in
the ideal average accounting, with 80 jobs admitted per unit time. These are LP
reference values, not measured stationary occupancies of the finite simulation.
Their exact combination of full mean occupancy and zero blocking is not an
attainable finite-system steady state under the paper's Poisson loss model.
The finite simulator may block jobs and truncate their target allocations.

The associated arrival probabilities are
`p_3 = s_3*y_3/lambda = 0.625` and `p_4 = s_4*y_4/lambda = 0.375`.
They differ from the occupancy values because jobs with larger speedups spend
less time in the system.

If exponential inherent sizes have configured mean `m` instead, the simulator
uses arrival intensity `n*lambda/m` and completion rate `s_i/m`. Equation (3)
still holds after cancelling `m`, while the execution-time formula becomes
`E[D] = m * sum_i E[x_i] / (lambda*(1-P_b))`.


## Optimal allocation calculations

These notes give a formal derivation of the single-class allocation rule in
Section III, Theorem 1, and equations (7)-(10), followed by the probability
conversion in Section IV. Labels such as **Lemma A1** and **Proposition A1**
belong to these notes; they are not the paper's numbering. In particular,
Proposition A1 below is a feasibility result, not the paper's Proposition 1
about stochastic asymptotic optimality.

The proof order is: decreasing efficiencies, LP feasibility, a two-component
optimizer, a supporting-line bound, optimal target selection, and the conversion
from state to probabilities and mean execution time.

### Assumptions and notation

Fix a system size `n` and a positive integer maximum allocation `d`; suppress
the paper's superscript `(n)`. There are `n` identical servers. A job using `i`
servers keeps that allocation until completion and executes for `X / s_i`,
where `X` is its inherent size and `m = E[X]` is finite and positive. All jobs
share the same speedup curve. The loss system has no waiting queue.

Throughout the allocation theorem, assume

$$
 s_0=0,\qquad s_1=1,\qquad
 \Delta_i:=s_i-s_{i-1}>0,\qquad
 \Delta_{i+1}\le\Delta_i\quad(1\le i<d),\qquad 0<\rho<1.
$$

Thus speedups are strictly increasing and discretely concave, including the
initial gain `Delta_1 = 1`. Concavity is not required to be strict. With total
arrival intensity `a`, define normalized offered load and efficiency by

$$
 \rho:=\frac{am}{n},\qquad e_i:=\frac{s_i}{i}.
$$

Here `rho` is offered one-server work per server per unit time, not the actual
occupied fraction. In the paper, `m = 1` and `rho = lambda(n)`; in code it is
`normalized_load`. Poisson arrivals and independent, unit-mean exponential job
sizes are assumptions of the paper's stochastic analysis. They are not needed
for the deterministic LP proofs below. The probability interpretation uses a
target selected independently of the arriving job's size.

### The optimal state is not a probability distribution

**Definition A1 (Allocation LP).** Let `y_i >= 0` represent a target steady-state
expected number of jobs using `i` servers, divided by `n`. Define

$$
 Z(y):=\sum_{i=1}^{d}y_i,\qquad
 U(y):=\sum_{i=1}^{d}i y_i,\qquad
 R(y):=\sum_{i=1}^{d}s_i y_i.
$$

These are jobs per server, occupied-server fraction, and normalized throughput.
The ideal zero-blocking allocation problem is

$$
 \min_{y\in\mathcal F_\rho} D(y),\qquad
 D(y):=\frac{m}{\rho}Z(y),\qquad
 \mathcal F_\rho:=\{y\in\mathbb R_+^d:R(y)=\rho,\ U(y)\le1\}.
$$

For `m = 1` this is equation (7). Multiplying its objective by positive `m`
restores time units and does not change its minimizers. The service and capacity
constraints express the reference state with all offered work served; they do
not assert that every feasible vector is achievable by a finite stochastic
system. Proposition A3 and Corollary A1 below derive its job-level meaning.

**Lemma A1 (Efficiencies decrease).** Under the speedup assumptions,

$$
 1=e_1\ge e_2\ge\cdots\ge e_d>0,\qquad s_i\le i.
$$

Moreover, if `e_k < 1` and `k < d`, then `e_(k+1) < e_k`.

*Proof.* Since `s_i = sum_(r=1)^i Delta_r`, efficiency is an average:

$$
 e_i=\frac1i\sum_{r=1}^{i}\Delta_r.
$$

Every gain in this average is at least `Delta_(i+1)`, so

$$
 e_{i+1}=\frac{i e_i+\Delta_{i+1}}{i+1}\le e_i.
$$

Positivity and `e_1 = 1` give the remaining inequalities. Equality
`e_(k+1) = e_k` would require `Delta_(k+1) = e_k`. All of the first `k` gains
are at least this value and average to it, so they must all equal it. In
particular, `e_k = Delta_1 = 1`. Thus equality is impossible when `e_k < 1`.
This proves the strict assertion. □

**Proposition A1 (Feasibility and existence).** For any positive `rho`, the LP
has a feasible solution, and hence a minimizer, if and only if `rho <= 1`.

*Proof.* Lemma A1 implies that any feasible `y` satisfies

$$
 \rho=R(y)=\sum_i s_i y_i\le\sum_i i y_i=U(y)\le1.
$$

Conversely, if `0 < rho <= 1`, the vector `y_1 = rho`, with all other components
zero, is feasible because `s_1 = 1`. Also, every feasible component satisfies
`0 <= y_i <= 1/i`. The feasible set is closed and bounded in finite dimension,
so it is compact. The continuous objective attains its minimum there. □

The mathematical feasibility boundary includes `rho = 1`, as does the paper's
Theorem 1. The implementation requires `rho < 1`. At `rho = 0`, the displayed
objective and the probability conversion divide by zero; above one the
zero-blocking LP is infeasible.

### Why one target or two neighbouring targets suffice

**Lemma A2 (At most two positive components suffice).** There is an optimal
state `y*` with at most two positive components.

*Proof.* Among the minimizers supplied by Proposition A1, choose one with the
fewest positive components. Suppose its support `S = {i : y_i > 0}` has at least
three indices. Two homogeneous linear equations in at least three unknowns
have a nonzero solution `h`, supported on `S`, satisfying

$$
 \sum_{i\in S}s_i h_i=0,\qquad \sum_{i\in S}i h_i=0.
$$

For sufficiently small positive `epsilon`, both `y + epsilon*h` and
`y - epsilon*h` remain nonnegative, and both preserve throughput and occupancy.
If `sum(h_i)` were nonzero, one direction would decrease `Z(y)` and contradict
optimality. Hence `sum(h_i) = 0`, so the objective is constant along this line.

The second equation forces `h` to have both signs. Increase `t` from zero in
`y + t*h` until the first positive component becomes zero, namely at
`t = min_{h_i < 0} y_i / (-h_i)`. This produces a feasible optimizer with fewer
positive components and no new ones, contradicting our choice of `y`. Thus
there is an optimizer with at most two positive components. □

This lemma uses linear constraints and positivity. It does not show that the
two indices can be chosen adjacent; concavity supplies that additional result.

**Lemma A3 (Supporting line and lower bound).** Fix `k < d` and put

$$
 b:=s_{k+1}-s_k>0,\qquad
 c:=s_k-kb=k(k+1)(e_k-e_{k+1}).
$$

Then `s_j <= c + bj` for every `j`. If `e_k > e_(k+1)`, so `c > 0`, every
feasible state satisfies

$$
 Z(y)\ge\frac{\rho-b}{c}.
$$

A feasible state supported on `{k, k+1}` with `U(y) = 1` attains this bound.

*Proof.* For `j < k`, concavity gives

$$
 s_k-s_j=\sum_{r=j+1}^{k}\Delta_r\ge(k-j)b,
$$

which rearranges to `s_j <= c + bj`. For `j > k+1`, concavity similarly gives

$$
 s_j-s_{k+1}=\sum_{r=k+2}^{j}\Delta_r\le(j-k-1)b,
$$

and hence the same inequality. Equality holds at `j = k` and `j = k+1` by
construction. Therefore, for any feasible `y`,

$$
 \rho=R(y)\le\sum_j(c+bj)y_j=cZ(y)+bU(y)\le cZ(y)+b.
$$

Dividing by positive `c` proves the lower bound. If only the two touching
indices have positive components and `U(y) = 1`, both inequalities are
equalities. □

**Theorem A1 (Optimal target selection).** Assume `0 < rho < 1`. An optimal
state can be chosen as follows.

1. If `rho <= e_d`, choose only target `d`:

$$
 y_d^*=\frac{\rho}{s_d},\qquad y_j^*=0\quad(j\ne d).
$$

This state is the unique minimizer.

2. Otherwise, if `rho = e_k` for some `k`, choose the largest matching index
   and use only target `k`:

$$
 y_k^*=\frac1k=\frac{\rho}{s_k},\qquad y_j^*=0\quad(j\ne k).
$$

This is an optimal state; uniqueness is not asserted under weak concavity.

3. In every other case, there is a `k < d` such that
   `e_(k+1) < rho < e_k`. Use the neighbouring targets `k` and `k+1`:

$$
 y_k^*=\frac{\rho-e_{k+1}}{k(e_k-e_{k+1})},\qquad
 y_{k+1}^*=\frac{e_k-\rho}{(k+1)(e_k-e_{k+1})},\qquad
 y_j^*=0\quad(j\notin\{k,k+1\}).
$$

*Proof.* In case 1, capacity use is `d*rho/s_d = rho/e_d <= 1`, so the displayed
state is feasible. Every feasible state satisfies

$$
 \rho=\sum_j s_jy_j\le s_d\sum_jy_j,
 \qquad D(y)\ge\frac{m}{s_d}.
$$

The displayed state attains equality. Since `s_j < s_d` for every `j < d`,
equality forces all those components to vanish, proving uniqueness.

In case 2, the singleton satisfies `R(y*) = s_k/k = rho` and `U(y*) = 1`.
Case 1 has already covered `k = d`. Otherwise `e_k = rho < 1`, so Lemma A1
gives `e_(k+1) < e_k`. Lemma A3 applies with `c > 0`, and the singleton attains
its lower bound. It therefore minimizes `Z`, and hence `D`.

For case 3, ordered efficiencies and `e_1 = 1 > rho > e_d` give a bracketing
pair when there is no exact boundary. Let `g = e_k - e_(k+1) > 0`. The displayed
components are positive and satisfy

$$
 U(y^*)=\frac{\rho-e_{k+1}}g+\frac{e_k-\rho}g=1,
$$

$$
 R(y^*)=e_k\frac{\rho-e_{k+1}}g
          +e_{k+1}\frac{e_k-\rho}g=\rho.
$$

They are therefore feasible. They are also precisely the solution of

$$
 s_k y_k+s_{k+1}y_{k+1}=\rho,\qquad
 k y_k+(k+1)y_{k+1}=1.
$$

Lemma A3 shows that they attain a lower bound valid for every feasible state,
so they are globally optimal. At either endpoint of the interval, one
component becomes zero, recovering the corresponding singleton. These cases
exhaust the possible loads. □

**Proposition A2 (A sufficient condition for uniqueness).** In case 2 or 3 of
Theorem A1, use the supporting line from its proof. If

$$
 s_j<c+bj\qquad\text{for every }j\notin\{k,k+1\},
$$

then the displayed optimal state is unique. Strictly decreasing gains are a
sufficient condition for these strict inequalities.

*Proof.* Every optimizer must attain the same bound in Lemma A3. Equality in
the first inequality requires zero weight at every point strictly below the
line. Equality in the second requires `U(y) = 1` because `b > 0`. Thus any
optimizer is supported on `{k, k+1}` and solves the two equations in Theorem A1.
Their coefficient determinant is `(k+1)*s_k - k*s_(k+1) = c > 0`, so the solution
is unique. If gains strictly decrease, both sums used in Lemma A3 are strict
away from the two touching points, proving the stated sufficient condition. □

**Counterexample A1 (Weak concavity does not imply uniqueness).** Take speedups
`(1, 1.8, 2.6)` and `rho = 0.9 = e_2`. The gains `(1, 0.8, 0.8)` are positive
and nonincreasing. Both states

$$
 y=(0,\tfrac12,0),\qquad
 \widetilde y=(\tfrac14,0,\tfrac14)
$$

satisfy `R = 0.9`, `U = 1`, and `Z = 0.5`. The line `s_j = 0.2 + 0.8*j`
touches all three speedup points, so Lemma A3 gives `Z >= 0.5`. Both states are
therefore optimal, with `D = 5*m/9`. The code's singleton choice remains valid.
This conflicts with the paper's Theorem 1(ii) uniqueness wording under P1-P2;
clarification with Arpan remains pending.

**Counterexample A2 (Decreasing efficiency is insufficient for adjacency).**
Take speedups `(1, 1.5, 2.1)` and `rho = 0.8`. Efficiencies are decreasing,
`(1, 0.75, 0.7)`, but gains `(1, 0.5, 0.6)` violate concavity. The threshold
neighbours `1, 2` give state `(1/5, 2/5, 0)` and objective `3*m/4`. Instead,

$$
 y=(\tfrac13,0,\tfrac29)
$$

is feasible and has objective `25*m/36 < 3*m/4`. It is globally optimal:
the line `s_j <= 9/20 + (11/20)*j` bounds all three points, so the same
inequality as in Lemma A3 gives `Z >= 5/9`, attained by this state. Thus an
optimal pair can skip an intermediate target when concavity is absent.

### From the optimal state to arrival probabilities

**Proposition A3 (State-to-probability conversion).** For any feasible state `y`,

$$
 p_i:=\frac{s_i y_i}{\rho}
$$

is a probability vector with the same positive support as `y`. It is the unique
vector consistent with `y` in the ideal balance calculation where every arrival
is admitted, every selected target is achieved, and targets are independent of
job size.

*Proof.* All entries are nonnegative, and service balance gives

$$
 \sum_i p_i=\frac{\sum_i s_i y_i}{\rho}=1.
$$

Since `s_i > 0` and `rho > 0`, `p_i > 0` exactly when `y_i > 0`.
For the interpretation, allocation-`i` arrivals have intensity
`a*p_i = n*rho*p_i/m` and mean duration `m/s_i`. Allocation-specific Little's
law gives

$$
 n y_i=\frac{n\rho p_i}{m}\frac{m}{s_i},\qquad
 y_i=\frac{\rho p_i}{s_i}.
$$

Solving for `p_i` gives the asserted unique formula. This is a balance
identity, not a proof that a finite system realizes the ideal state. □

The values `y_i` are jobs per server, not probabilities. Even `y_i / Z(y)`
describes the proportions among jobs currently running; longer jobs are more
likely to be present. The speedup factor in Proposition A3 converts these
occupancy counts to arrival proportions. Apply it to `y*` to obtain `p*`.

**Corollary A1 (Mean execution-time benchmark).** With job size independent of
the target and every selected target achieved,

$$
 D^*=m\sum_i\frac{p_i^*}{s_i}=\frac{m}{\rho}\sum_i y_i^*.
$$

*Proof.* Conditional on target `i`, mean execution time is `m/s_i`. Averaging
over targets gives the first expression. Substituting `p_i* = s_i*y_i*/rho`
gives the second, which is the LP objective. □

**Corollary A2 (Linear speedups).** If `s_i = i` for every `i`, the optimal
choice is target `d` with probability one, and `D* = m/d`.

*Proof.* Every efficiency equals one. Since `rho < 1`, case 1 of Theorem A1
applies. Proposition A3 gives `p_d* = s_d*(rho/s_d)/rho = 1`, and Corollary A1
gives `D* = m/s_d = m/d`. □

### Worked example and implementation

For `rho = 0.8` and speedups `(1, 1.8, 2.5, 3, 3.4)`,

$$
 e_4=\frac34<\frac45<\frac56=e_3.
$$

Theorem A1 gives targets `3, 4`, with `y_3* = 1/5` and `y_4* = 1/10`. Check:

$$
 \frac52\frac15+3\frac1{10}=\frac45,\qquad
 3\frac15+4\frac1{10}=1.
$$

Proposition A3 gives `p_3* = 5/8` and `p_4* = 3/8`. Corollary A1 gives
`D* = 3*m/8`, or `0.375` at unit mean size. The supporting line for this pair
has `b = 1/2` and `c = 1`, certifying `Z >= rho - 1/2 = 3/10`, which the state
attains. Doubling `m` doubles the time benchmark and halves arrival intensity at
fixed `rho`, leaving the optimal target distribution unchanged.

In [allocation.py](../scheduling/allocation.py), `optimal_allocation_targets()`
implements Theorem A1, `optimal_allocation_probabilities()` implements
Proposition A3, and `optimal_mean_execution_time()` implements Corollary A1.
Inputs are checked once in main.py. A four-ulp tolerance handles boundary
rounding below one; unit efficiency is never rounded into equality for an
admissible load. Paired probabilities are normalized for floating-point round-off.

The deterministic results require the speedup and load assumptions above.
Poisson/exponential assumptions enter the paper's stochastic proofs, while
finite positive `m` and target/size independence support the probability and
time interpretations. Strict concavity is unnecessary for existence of an
optimal neighbouring pair; it supplies a sufficient uniqueness condition.

`RandomizedPolicy.optimal()` uses `p*` as its target distribution. On an arrival with `j` idle servers,
the policy samples target `i` and allocates `min(i, j)`, blocking only when
`j = 0`. Actual finite-system allocation probabilities can therefore differ
from `p*`. None of the statements above proves convergence of that policy to
`y*`, vanishing blocking, or attainment of `D*`. These require the separate
stochastic results and scaling assumptions. The [Proposition 1 notes](theory.md)
show what convergence to the LP state would imply and why Appendix A needs
extra care when maximum parallelism grows. Theorem 2 separately concerns
convergence under the paper's policy. Unit-load LP feasibility does not imply
zero blocking in a finite system.

## Execution and completion

- The simulator accepts any `AllocationPolicy` with `reset()` and
  `choose_allocation(idle_servers)`. The policy resets for a fresh run and
  chooses an allocation for each arrival. ServerPool enforces capacity and
  allocation limits.
- main.py holds the run configuration. Simulator and ServerPool receive server
  count and speedups explicitly; reusable modules do not import the entry point.
- main.py checks configuration once before generating jobs. Internal components
  trust these settings and valid generated jobs. Job is a frozen dataclass with
  no runtime validation; generated IDs are unique and arrivals are ordered.
  Runtime checks retain allocation limits, arrival-time ordering and finite
  completion times. Mathematical and conservation checks remain in the tests.
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
