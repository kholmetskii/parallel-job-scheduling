## **1 Optimal allocation calculations**

### **1.1 Assumptions and notation**

***Definition***

Let $d\in\mathbb N$ and let

$$
s:\{0,\ldots,d\}\longrightarrow[0,\infty),
\qquad s_i:=s(i),
$$

be a speedup function. Assume

$$
s_0=0,\qquad s_1=1.
$$

For $i\in\{1,\ldots,d\}$, define the marginal gain and allocation efficiency by

$$
\Delta_i:=s_i-s_{i-1},
\qquad
e_i:=\frac{s_i}{i}.
$$

The speedup function is **strictly increasing** if $\Delta_i\gt 0$ for every $i$, and **discretely concave** if

$$
\Delta_{i+1}\le\Delta_i
\qquad (1\le i\lt d).
$$

***Definition***

Let $n\in\mathbb N$ be the number of identical servers and let $a\gt 0$ be the total arrival intensity. On a probability space $(\Omega,\mathcal F,\mathbb P)$, let

$$
X:\Omega\longrightarrow[0,\infty)
$$

be a job's inherent execution time, with

$$
m:=\mathbb E[X]\in(0,\infty).
$$

If the job receives $i$ servers with speedup $s_i\gt 0$, its execution time is $X/s_i$. The **normalized offered load** is

$$
\rho:=\frac{am}{n}.
$$

***Remark***

Let $\rho=am/n$ be normalized offered load. It measures offered one-server work per server per unit time; it is not the occupied-server fraction.

The allocation rule implemented in the project assumes $0\lt \rho\lt 1$. The deterministic LP also permits $\rho=1$. At $\rho=0$, the objective and probability formulas below involve division by zero.

***Remark***

For the allocation results below, the labels A1, A2, and so forth are local to these notes. They are separate from the paper's numbering. In particular, Proposition A1 below concerns LP feasibility; it is not the paper's Proposition 1 concerning asymptotic optimality.

### **1.2 The optimal state is not a probability distribution**

***Definition***

**A1 (Allocation LP).** Let $d\in\mathbb N$, $m,\rho\gt 0$, and $s_1,\ldots,s_d\gt 0$. For $y=(y_1,\ldots,y_d)\in[0,\infty)^d$, define

$$
Z(y):=\sum_{i=1}^{d}y_i,
\qquad
U(y):=\sum_{i=1}^{d}i y_i,
\qquad
R(y):=\sum_{i=1}^{d}s_i y_i.
$$

Here $y_i$ represents a target steady-state expected number of jobs using $i$ servers, divided by the total server count. Thus:

- $Z(y)$ is the expected number of jobs per server;
- $U(y)$ is the expected occupied-server fraction;
- $R(y)$ is normalized throughput.

Define

$$
\mathcal F_\rho
:=
\left\{
y\in[0,\infty)^d:
R(y)=\rho,\ U(y)\le1
\right\}.
$$

The **allocation LP** is

$$
\min_{y\in\mathcal F_\rho}D(y),
\qquad
D(y):=\frac{m}{\rho}Z(y).
$$

***Remark***

Let $\mathcal F_\rho$ be the feasible set in Definition A1. The constraint $R(y)=\rho$ describes the ideal balance in which all offered work is served. Membership in $\mathcal F_\rho$ does not establish that a finite stochastic loss system can realize $y$ with zero blocking.

***Lemma***

**A1 (Efficiencies decrease).** Let $d\in\mathbb N$, and assume

$$
s_0=0,\qquad s_1=1,\qquad
\Delta_1\ge\Delta_2\ge\cdots\ge\Delta_d\gt 0,
$$

where $\Delta_i=s_i-s_{i-1}$. Then

$$
1=e_1\ge e_2\ge\cdots\ge e_d\gt 0,
\qquad s_i\le i,
$$

where $e_i=s_i/i$.

Moreover, if $k\lt d$ and $e_k\lt 1$, then $e_{k+1}\lt e_k$.

***Proof***

Since $s_i=\sum_{r=1}^{i}\Delta_r$,

$$
e_i=\frac1i\sum_{r=1}^{i}\Delta_r.
$$

Each of the first $i$ gains is at least $\Delta_{i+1}$. Therefore

$$
e_{i+1}
=\frac{i e_i+\Delta_{i+1}}{i+1}
\le e_i.
$$

Together with $e_1=\Delta_1=1$ and positivity, this gives the stated ordering and $s_i=i e_i\le i$.

If $e_{k+1}=e_k$, then $\Delta_{k+1}=e_k$. The first $k$ gains are all at least this value and have average $e_k$, so they all equal $e_k$. In particular,

$$
e_k=\Delta_1=1.
$$

Thus $e_k\lt 1$ implies $e_{k+1}\lt e_k$. $\square$

***Proposition***

**A1 (Feasibility and existence).** Let $d\in\mathbb N$, $m,\rho\gt 0$, and assume

$$
s_0=0,\qquad s_1=1,\qquad
\Delta_1\ge\cdots\ge\Delta_d\gt 0.
$$

Let

$$
\mathcal F_\rho
=
\left\{
y\in[0,\infty)^d:
\sum_i s_i y_i=\rho,\
\sum_i i y_i\le1
\right\}.
$$

Then the allocation LP

$$
\min_{y\in\mathcal F_\rho}\frac{m}{\rho}\sum_i y_i
$$

has a minimizer if and only if $\rho\le1$.

***Proof***

For any feasible $y$, Lemma A1 gives

$$
\rho=\sum_i s_i y_i
\le\sum_i i y_i
\le1.
$$

Hence feasibility requires $\rho\le1$.

Conversely, if $0\lt \rho\le1$, then

$$
y=(\rho,0,\ldots,0)
$$

is feasible because $s_1=1$.

Every feasible component satisfies $0\le y_i\le1/i$. Hence $\mathcal F_\rho$ is closed and bounded in $\mathbb R^d$, and therefore compact. The objective is continuous, so it attains its minimum. $\square$

### **1.3 Why one target or two neighbouring targets suffice**

***Lemma***

**A2 (At most two positive components suffice).** Let $d\in\mathbb N$, $\rho\gt 0$, and $s_1,\ldots,s_d\gt 0$. Assume

$$
\mathcal F_\rho
=
\left\{
y\in[0,\infty)^d:
\sum_i s_i y_i=\rho,\
\sum_i i y_i\le1
\right\}
\ne\varnothing.
$$

Then $\min_{y\in\mathcal F_\rho}\sum_i y_i$ has an optimizer with at most two positive components.

***Proof***

The feasible set is compact, so a minimizer exists. Choose a minimizer $y$ with the fewest positive components, and write

$$
S:=\{i:y_i\gt 0\}.
$$

Suppose $|S|\ge3$. There is a nonzero vector $h\in\mathbb R^d$, supported on $S$, satisfying

$$
\sum_i s_i h_i=0,
\qquad
\sum_i i h_i=0,
$$

because these are two homogeneous linear equations in at least three unknowns.

For sufficiently small $\varepsilon\gt 0$, both $y+\varepsilon h$ and $y-\varepsilon h$ remain feasible. If $\sum_i h_i\ne0$, one direction decreases the objective. Therefore optimality requires

$$
\sum_i h_i=0.
$$

Since $\sum_i i h_i=0$ and $h\ne0$, the vector $h$ has both positive and negative components. Set

$$
t:=\min_{i:h_i\lt 0}\frac{y_i}{-h_i}\gt 0.
$$

Then $y+t h$ remains feasible, has the same objective, and has fewer positive components than $y$. This contradicts the choice of $y$. Hence $|S|\le2$. $\square$

***Remark***

For the LP in Lemma A2, the two-component conclusion follows from its linear constraints. It does not establish adjacency of the selected indices. Concavity provides that additional conclusion through Lemma A3.

***Lemma***

**A3 (Supporting line and lower bound).** Let $d\ge2$, and assume

$$
s_0=0,\qquad s_1=1,\qquad
\Delta_1\ge\cdots\ge\Delta_d\gt 0.
$$

Let $k\in\{1,\ldots,d-1\}$, and define

$$
b:=s_{k+1}-s_k,
\qquad
c:=s_k-kb.
$$

Then

$$
s_j\le c+bj
\qquad (1\le j\le d).
$$

Moreover,

$$
c=k(k+1)(e_k-e_{k+1}).
$$

If $e_k\gt e_{k+1}$, then every feasible state

$$
y\ge0,\qquad
\sum_j s_jy_j=\rho,\qquad
\sum_j j y_j\le1
$$

satisfies

$$
Z(y):=\sum_j y_j\ge\frac{\rho-b}{c}.
$$

A feasible state supported on $\{k,k+1\}$ with full occupancy attains this bound.

***Proof***

Here $b=\Delta_{k+1}\gt 0$. If $j\lt k$, concavity gives

$$
s_k-s_j
=\sum_{r=j+1}^{k}\Delta_r
\ge(k-j)b.
$$

Hence $s_j\le s_k-(k-j)b=c+bj$.

If $j\gt k+1$, concavity gives

$$
s_j-s_{k+1}
=\sum_{r=k+2}^{j}\Delta_r
\le(j-k-1)b,
$$

which yields the same bound. Equality holds at $j=k,k+1$.

Also,

$$
c=(k+1)s_k-k s_{k+1}
=k(k+1)(e_k-e_{k+1}).
$$

When $e_k\gt e_{k+1}$, we have $c\gt 0$. Thus every feasible $y$ satisfies

$$
\rho
=\sum_j s_jy_j
\le c\sum_j y_j+b\sum_j j y_j
\le cZ(y)+b.
$$

Rearranging proves the lower bound.

If $y$ is supported on the two touching indices and $\sum_j j y_j=1$, both inequalities are equalities. $\square$

***Theorem***

**A1 (Optimal target selection).** Let $d\in\mathbb N$, $m\gt 0$, and $0\lt \rho\lt 1$. Assume

$$
s_0=0,\qquad s_1=1,\qquad
\Delta_1\ge\cdots\ge\Delta_d\gt 0.
$$

Define $e_i=s_i/i$. Consider

$$
\min_{y\in[0,\infty)^d}\frac{m}{\rho}\sum_i y_i
$$

subject to

$$
\sum_i s_i y_i=\rho,
\qquad
\sum_i i y_i\le1.
$$

An optimal state can be chosen according to the following cases.

1. **Light load:** if $\rho\le e_d$, the unique optimizer is

   $$
   y_d^*=\frac{\rho}{s_d},
   \qquad
   y_j^*=0\quad(j\ne d).
   $$

2. **Efficiency boundary:** otherwise, if $\rho=e_k$, choose the largest matching index $k$. An optimizer is

   $$
   y_k^*=\frac1k=\frac{\rho}{s_k},
   \qquad
   y_j^*=0\quad(j\ne k).
   $$

3. **Between efficiencies:** otherwise, there is $k\lt d$ such that

   $$
   e_{k+1}\lt \rho\lt e_k.
   $$

   An optimizer is

   $$
   y_k^*
   =\frac{\rho-e_{k+1}}{k(e_k-e_{k+1})},
   \qquad
   y_{k+1}^*
   =\frac{e_k-\rho}{(k+1)(e_k-e_{k+1})},
   $$

   with $y_j^*=0$ for $j\notin\{k,k+1\}$.

***Proof***

**Case 1.** The proposed state has throughput $\rho$ and occupancy

$$
d y_d^*=\frac{\rho}{e_d}\le1.
$$

Every feasible $y$ satisfies

$$
\rho=\sum_j s_jy_j\le s_d\sum_j y_j,
$$

so

$$
D(y)\ge\frac{m}{s_d}.
$$

The proposed state attains equality. Since $s_j\lt s_d$ for $j\lt d$, equality forces $y_j=0$ for all $j\lt d$. This proves uniqueness.

**Case 2.** The proposed singleton satisfies

$$
s_k y_k^*=\frac{s_k}{k}=\rho,
\qquad
k y_k^*=1.
$$

The case $k=d$ is already covered by Case 1. Otherwise, $\rho=e_k\lt 1$, so Lemma A1 gives $e_{k+1}\lt e_k$. Lemma A3 applies, and the singleton attains its lower bound. Hence it is optimal.

**Case 3.** Since

$$
e_1=1\gt \rho\gt e_d
$$

and the efficiencies are ordered, absence of an exact boundary gives a bracketing pair.

Write $g:=e_k-e_{k+1}\gt 0$. The proposed components are positive, and

$$
k y_k^*+(k+1)y_{k+1}^*
=\frac{\rho-e_{k+1}+e_k-\rho}{g}
=1.
$$

Their throughput is

$$
s_k y_k^*+s_{k+1}y_{k+1}^*
=
\frac{e_k(\rho-e_{k+1})
+e_{k+1}(e_k-\rho)}{g}
=\rho.
$$

Thus they are feasible. They are the solution of

$$
s_k y_k+s_{k+1}y_{k+1}=\rho,
\qquad
k y_k+(k+1)y_{k+1}=1.
$$

By Lemma A3, they attain a lower bound valid for every feasible state. Therefore they are globally optimal.

At either endpoint of the interval, one component becomes zero, recovering the corresponding singleton. $\square$

***Proposition***

**A2 (A sufficient condition for uniqueness).** Let $d\ge2$, $m,\rho\gt 0$, $s_1,\ldots,s_d\gt 0$, and $k\in\{1,\ldots,d-1\}$. Define

$$
b:=s_{k+1}-s_k\gt 0,
\qquad
c:=s_k-kb\gt 0.
$$

Assume

$$
s_j\lt c+bj
\qquad
\text{for }j\notin\{k,k+1\}.
$$

Suppose a feasible state $y^*$ satisfies

$$
\operatorname{supp}(y^*)\subseteq\{k,k+1\},
\qquad
\sum_j j y_j^*=1.
$$

Then $y^*$ is the unique minimizer of the allocation LP.

For the speedup curves in Theorem A1, strictly decreasing marginal gains are sufficient for the strict supporting-line inequalities.

***Proof***

The supporting-line calculation gives

$$
\rho\le cZ(y)+bU(y)\le cZ(y)+b.
$$

The state $y^*$ attains equality, so every optimizer must attain equality.

Equality in the first inequality forces zero weight at every point strictly below the line. Equality in the second forces $U(y)=1$, because $b\gt 0$. Consequently, every optimizer is supported on $\{k,k+1\}$ and solves

$$
s_k y_k+s_{k+1}y_{k+1}=\rho,
\qquad
k y_k+(k+1)y_{k+1}=1.
$$

The coefficient determinant is

$$
(k+1)s_k-k s_{k+1}=c\gt 0,
$$

so this system has a unique solution.

If marginal gains strictly decrease, the comparisons in the proof of Lemma A3 are strict away from $k,k+1$. Hence only those two speedup points touch the line. $\square$

***Example***

**A1 (Weak concavity does not imply uniqueness).** Let

$$
(s_1,s_2,s_3)=\left(1,\frac95,\frac{13}{5}\right),
\qquad
\rho=\frac9{10},
\qquad m\gt 0.
$$

The marginal gains are

$$
\left(1,\frac45,\frac45\right),
$$

so the speedups are strictly increasing and concave.

Both states

$$
y=\left(0,\frac12,0\right),
\qquad
\widetilde y=\left(\frac14,0,\frac14\right)
$$

have throughput $9/10$, occupancy $1$, and $Z=1/2$.

All three speedup points lie on

$$
s_j=\frac15+\frac45j.
$$

Therefore every feasible state satisfies

$$
\frac9{10}\le\frac15Z+\frac45,
\qquad
Z\ge\frac12.
$$

Both states are optimal, with objective

$$
D=\frac{m}{9/10}\frac12=\frac{5m}{9}.
$$

Thus an optimal singleton exists at an efficiency boundary, but need not be the unique optimizer.

***Example***

**A2 (Decreasing efficiency does not imply adjacency).** Let

$$
(s_1,s_2,s_3)=\left(1,\frac32,\frac{21}{10}\right),
\qquad
\rho=\frac45,
\qquad m\gt 0.
$$

The efficiencies decrease:

$$
(e_1,e_2,e_3)=\left(1,\frac34,\frac7{10}\right),
$$

but the marginal gains

$$
\left(1,\frac12,\frac35\right)
$$

violate concavity.

The threshold neighbours $1,2$ give the feasible state

$$
y=\left(\frac15,\frac25,0\right),
\qquad
D(y)=\frac{3m}{4}.
$$

The non-neighbouring targets $1,3$ give

$$
\widetilde y=\left(\frac13,0,\frac29\right),
\qquad
D(\widetilde y)=\frac{25m}{36}\lt \frac{3m}{4}.
$$

Moreover,

$$
s_j\le\frac9{20}+\frac{11}{20}j
\qquad(j=1,2,3).
$$

Every feasible state therefore satisfies

$$
\frac45\le\frac9{20}Z+\frac{11}{20},
\qquad
Z\ge\frac59.
$$

The state $\widetilde y$ attains this bound and is globally optimal. Hence decreasing efficiency alone does not justify selecting neighbouring targets.

### **1.4 From the optimal state to arrival probabilities**

***Proposition***

**A3 (State-to-probability conversion).** Let $d\in\mathbb N$, $\rho\gt 0$, and $s_1,\ldots,s_d\gt 0$. Let $y\in[0,\infty)^d$ satisfy

$$
\sum_{i=1}^{d}s_i y_i=\rho.
$$

Define

$$
p_i:=\frac{s_i y_i}{\rho}.
$$

Then $p=(p_1,\ldots,p_d)$ is a probability vector, and

$$
p_i\gt 0\iff y_i\gt 0.
$$

For an ideal stationary balance calculation with $n$ servers, mean inherent job size $m\gt 0$, arrival intensity $n\rho/m$, no blocking, and every independently sampled target achieved, this is the unique arrival-target distribution consistent with normalized mean occupancies $y_i$.

***Proof***

Since $s_i\gt 0$, $y_i\ge0$, and $\rho\gt 0$,

$$
p_i\ge0,
\qquad
\sum_i p_i=\frac{\sum_i s_i y_i}{\rho}=1.
$$

The same positivity assumptions give equality of positive supports.

For the balance interpretation, jobs selecting target $i$ arrive at rate

$$
\frac{n\rho p_i}{m}.
$$

Independence between target and inherent job size gives mean duration $m/s_i$. Allocation-specific Little's law yields

$$
n y_i
=
\frac{n\rho p_i}{m}\frac{m}{s_i}
=
\frac{n\rho p_i}{s_i}.
$$

Solving for $p_i$ gives the stated formula uniquely. $\square$

***Remark***

Let $y\ge0$ satisfy $\sum_i s_i y_i=\rho\gt 0$, and let $p_i=s_i y_i/\rho$. The entries $y_i$ are normalized occupancy counts, not arrival probabilities.

The ratios

$$
\frac{y_i}{\sum_j y_j}
$$

describe allocation proportions among currently running jobs. Such proportions favour allocations with longer execution times. The factor $s_i$ converts occupancy counts into arrival proportions.

***Corollary***

**A1 (Mean execution-time benchmark).** Let $(\Omega,\mathcal F,\mathbb P)$ be a probability space. Let $X:\Omega\to[0,\infty)$ satisfy

$$
m:=\mathbb E[X]\in(0,\infty).
$$

Let $I:\Omega\to\{1,\ldots,d\}$ be independent of $X$, with

$$
\mathbb P(I=i)=p_i^*=\frac{s_i y_i^*}{\rho},
$$

where $s_i\gt 0$, $\rho\gt 0$, and $\sum_i s_i y_i^*=\rho$.

If every selected target is achieved, then

$$
D^*:=\mathbb E\!\left[\frac{X}{s_I}\right]
=
m\sum_i\frac{p_i^*}{s_i}
=
\frac{m}{\rho}\sum_i y_i^*.
$$

In particular, an optimal state $y^*$ gives the allocation LP's mean execution-time benchmark.

***Proof***

Independence gives

$$
\mathbb E\!\left[\frac{X}{s_I}\,\middle|\,I=i\right]
=\frac{m}{s_i}
$$

for each $i$ with positive probability. Therefore

$$
D^*
=\sum_i p_i^*\frac{m}{s_i}.
$$

Substitution of $p_i^*=s_i y_i^*/\rho$ gives

$$
D^*=\frac{m}{\rho}\sum_i y_i^*.
$$

$\square$

***Corollary***

**A2 (Linear speedups).** Let $d\in\mathbb N$, $m\gt 0$, and $0\lt \rho\lt 1$. Assume $s_i=i$ for $i=1,\ldots,d$. Then the allocation LP has the unique optimizer

$$
y_d^*=\frac{\rho}{d},
\qquad
y_j^*=0\quad(j\ne d).
$$

The associated target distribution and benchmark are

$$
p_d^*=1,
\qquad
D^*=\frac{m}{d}.
$$

***Proof***

Every efficiency equals one, so $\rho\lt 1=e_d$. Case 1 of Theorem A1 gives the unique optimizer. Proposition A3 yields

$$
p_d^*=\frac{d(\rho/d)}{\rho}=1.
$$

Corollary A1 then gives $D^*=m/d$. $\square$

### **1.5 Worked example and implementation**

***Example***

Let

$$
\rho=\frac45,
\qquad
(s_1,\ldots,s_5)
=\left(1,\frac95,\frac52,3,\frac{17}{5}\right),
\qquad m\gt 0.
$$

Since

$$
e_4=\frac34\lt \frac45\lt \frac56=e_3,
$$

Theorem A1 selects targets $3,4$, with

$$
y_3^*=\frac15,
\qquad
y_4^*=\frac1{10}.
$$

Their throughput and occupancy are

$$
\frac52\frac15+3\frac1{10}=\frac45,
\qquad
3\frac15+4\frac1{10}=1.
$$

The supporting line has

$$
b=s_4-s_3=\frac12,
\qquad
c=s_3-3b=1.
$$

Thus Lemma A3 gives

$$
Z(y)\ge\rho-\frac12=\frac3{10},
$$

which the proposed state attains.

Proposition A3 gives

$$
p_3^*=\frac58,
\qquad
p_4^*=\frac38.
$$

Consequently,

$$
D^*
=m\left(\frac{5/8}{5/2}+\frac{3/8}{3}\right)
=\frac{3m}{8}.
$$

For $m=1$, the benchmark is $0.375$.

***Algorithm***

Let $d\in\mathbb N$, $0\lt \rho\lt 1$, and let $s_0,\ldots,s_d$ satisfy the increasing, concave speedup assumptions of Theorem A1.

1. Compute the efficiencies $e_i=s_i/i$.
2. Select the optimal singleton or neighbouring pair using Theorem A1.
3. Compute the corresponding state components $y_i^*$.
4. Set

   $$
   p_i^*=\frac{s_i y_i^*}{\rho}.
   $$

5. On each arrival, sample $I\in\{1,\ldots,d\}$ with probabilities $p_i^*$.
6. If $J\in\{0,\ldots,n\}$ servers are idle, allocate

   $$
   \min(I,J)
   $$

   servers. Reject the job if $J=0$; otherwise retain its allocation until completion.

***Remark***

For the randomized algorithm above, $p_i^*$ is the probability of selecting target $i$. It need not equal the probability of actually receiving $i$ servers in a finite system, because idle capacity can truncate the selected target.

The deterministic LP proofs establish an optimal reference state and its associated target probabilities. They do not prove that the finite stochastic algorithm converges to that state or achieves vanishing blocking.

***Remark***

For the single-class loss-system model, Poisson arrivals and independent unit-mean exponential inherent execution times are assumptions of the paper's stochastic analysis. They are not required for the deterministic optimization proofs above.

The mean execution-time interpretation requires finite positive mean job size and independence between job size and sampled target. Strict concavity is unnecessary for existence of an optimal neighbouring pair; it provides a sufficient condition for uniqueness.

## **2 When does the optimal state imply optimal performance?**

Source: Mukhopadhyay et al., [Proposition 1 and Appendix A](https://doi.org/10.1109/TON.2025.3598595), printed pp. 387 and 393. The calculation below follows the paper's Poisson arrival and independent unit-mean exponential job-size model. It makes the scaling needed by Appendix A explicit.

### **2.1 The sufficient condition for fixed maximum parallelism**

Let $\lambda_n\in(0,1]$ be the normalized load, so the total arrival rate is $n\lambda_n$. Write $x^{(n)}_i$ for the stationary number of jobs running on $i$ servers, divided by $n$. Let $y^{*,(n)}$ solve LP (7), $D_n^*$ be its optimal objective, $B_n$ be the stationary blocking probability, and $T_n$ be the mean execution time of accepted jobs. Define

$$
\varepsilon_n=\mathbb E\bigl[\|x^{(n)}-y^{*,(n)}\|_1\bigr],
\qquad s_{\max,n}=\max_{1\le i\le d(n)}s_i.
$$

***Proposition (Appendix A with an explicit scaling condition)***

If $s_{\max,n}\varepsilon_n/\lambda_n\to0$, then $B_n\to0$ and $|T_n-D_n^*|\to0$. In particular, if $d(n)$ stays bounded and $\lambda_n$ stays bounded away from zero for large $n$, it is enough to show $\varepsilon_n\to0$.

***Proof***

For positive load the LP is feasible exactly when $\lambda_n\le1$: putting all its mass in component one gives $y_1=\lambda_n$ and uses at most one unit of capacity. Conversely, $s_i\le i$ implies $\sum_i s_i y_i\le\sum_i i y_i\le1$. Its feasible set is compact, so a minimum is attained; the component-one solution also gives $D_n^*\le1$.

At stationarity, the admitted arrival rate equals the departure rate. A job on $i$ servers departs at rate $s_i$. Dividing both rates by $n$ gives equation (3). The LP target satisfies the same service balance with zero blocking. Subtracting the balances yields

$$
\lambda_n B_n
=\sum_i s_i\bigl(y_i^{*,(n)}-\mathbb E[x_i^{(n)}]\bigr)
\le s_{\max,n}\varepsilon_n.
$$

By Little's law for accepted jobs, equation (4) is $\lambda_n(1-B_n)T_n=\sum_i\mathbb E[x_i^{(n)}]$. By the LP definition, $\lambda_n D_n^*=\sum_i y_i^{*,(n)}$. Subtracting, applying the triangle inequality, and using $D_n^*\le1$ gives

$$
|T_n-D_n^*|
\le\frac{\varepsilon_n/\lambda_n + B_n D_n^*}{1-B_n}
\le\frac{\varepsilon_n/\lambda_n+B_n}{1-B_n}.
$$

The assumed scaling gives $B_n\to0$. Since $s_{\max,n}\ge s_1=1$, it also gives $\varepsilon_n/\lambda_n\to0$. Both conclusions follow. For bounded $d(n)$, the paper's bound $s_{\max,n}\le d(n)$ and a positive lower bound on $\lambda_n$ give the simpler criterion. $\square$

For our fixed $d=5$ and the paper's three simulated regimes, the load is either the positive constant $0.8$ or tends to one. The simpler criterion therefore applies. It tells us **what state convergence would imply**; showing that the proposed policy actually has this convergence is separate work in Theorem 2.

### **2.2 Why the scaling matters when jobs can use more servers**

The unweighted error $\varepsilon_n$ counts jobs per server. A single job can occupy all $n$ servers while contributing only $1/n$ to this error. Appendix A multiplies the error by up to $d(n)$ to bound its effect on throughput. Thus $\varepsilon_n\to0$ alone cannot justify dropping that factor when $d(n)$ grows.

***Counterexample to the unqualified implication***

Take $d(n)=n$, linear speedups $s_i=i$, and constant load $\lambda_n=4/5$. Allocate all $n$ servers whenever a job arrives to an empty system. Starting empty, the only states are empty and full with one job. The transition rates are $4n/5$ into the full state and $n$ out of it. Poisson arrivals see the stationary full-state probability, so

$$
B_n=\frac{4n/5}{4n/5+n}=\frac49.
$$

With linear speedups the LP optimum uses only component $n$ and has $y_n^{*,(n)}=4/(5n)$. If $Z$ is the indicator of the full state, then $x_n^{(n)}=Z/n$ and the other components are zero. Hence

$$
\varepsilon_n
=\frac{1}{n}\left[\frac49\left(1-\frac45\right)+\frac59\frac45\right]
=\frac{8}{15n}\longrightarrow0,
$$

while blocking stays at $4/9$. The execution-time benchmark is attained here ($T_n=D_n^*=1/n$), but the vanishing-blocking requirement fails. This example is outside Theorem 2's separate assumption $d(n)=o(n)$; it qualifies the standalone wording of Proposition 1 and does not refute Theorem 2. Clarify with Arpan how Appendix A is intended to be applied when $d(n)$ grows.
