# M6: 100-server greedy experiment

Across 10 seeds, baseline blocking probability is **0.246470** (24.65%); mean execution time is **0.294275** time units.

## Settings and method

- Policy: greedy allocation, at most 5 servers per job; no waiting queue.
- Servers: 100; Poisson arrival rate: 80; exponential mean job size: 1.
- Speedups for 1–5 servers: 1, 1.8, 2.5, 3, 3.4.
- Seeds: 0–9, with a fresh workload generator and simulator for each run.
- Baseline: 10,000 warm-up arrivals, followed by 100,000 measured arrivals.
- Warm-up jobs keep their allocations but contribute no measurements. Measured accepted jobs contribute their full execution times.
- Every run retains server/job conservation checks and finishes all accepted jobs.
- Table means weight the ten run estimates equally. SD is the sample standard deviation across seeds, describing run-to-run variation; it is not a confidence interval.

## Results by configuration

| Warm-up arrivals | Measured arrivals | Runs | Blocking mean | Blocking SD | Execution mean | Execution SD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 100,000 | 10 | 0.246199 | 0.003667 | 0.294273 | 0.001202 |
| 5,000 | 100,000 | 10 | 0.246088 | 0.003243 | 0.294221 | 0.001064 |
| 10,000 | 10,000 | 10 | 0.244470 | 0.005002 | 0.292914 | 0.002162 |
| 10,000 | 50,000 | 10 | 0.246660 | 0.006063 | 0.294056 | 0.001543 |
| 10,000 | 100,000 | 10 | 0.246470 | 0.002799 | 0.294275 | 0.001011 |
| 10,000 | 200,000 | 10 | 0.246116 | 0.001737 | 0.294312 | 0.000614 |

## Sensitivity checks

Exploratory tolerances were set before running: 0.002 for the change in mean blocking probability (0.2 percentage points) and 0.002 time units for the change in mean execution time. These are practical comparison thresholds, not statistical significance tests.

The same seed produces a shared workload prefix across configurations. The table therefore pairs matching seeds. Delta means configuration minus baseline; delta SD describes variation in those paired differences.

| Warm-up | Measured | Blocking mean delta | Blocking delta SD | Execution mean delta | Execution delta SD |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 100,000 | -0.000271 | 0.001752 | -0.000001 | 0.000491 |
| 5,000 | 100,000 | -0.000382 | 0.001206 | -0.000054 | 0.000307 |
| 10,000 | 10,000 | -0.002000 | 0.004825 | -0.001360 | 0.002367 |
| 10,000 | 50,000 | +0.000190 | 0.003881 | -0.000219 | 0.001039 |
| 10,000 | 200,000 | -0.000354 | 0.002286 | +0.000037 | 0.000720 |

The checked mean changes are within the exploratory tolerances. Use 10,000 warm-up arrivals and 100,000 measured arrivals as the first greedy baseline.

The checks compare warm-ups of 1,000 and 5,000 with 10,000 at a fixed 100,000 measured arrivals, and compare 100,000 with 200,000 measured arrivals at a fixed 10,000 warm-up. Shorter 10,000- and 50,000-arrival runs also show how run-to-run variation changes with run length.

These finite checks support an initial baseline; they do not prove that all initialization bias has disappeared. Results apply to this model and parameter set. Further experiments may require greater precision.

## Baseline runs

| Seed | Measured accepted | Measured rejected | Blocking probability | Mean execution time |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 75,178 | 24,822 | 0.248220 | 0.294864 |
| 1 | 75,495 | 24,505 | 0.245050 | 0.294063 |
| 2 | 75,359 | 24,641 | 0.246410 | 0.293824 |
| 3 | 75,087 | 24,913 | 0.249130 | 0.295228 |
| 4 | 76,058 | 23,942 | 0.239420 | 0.292678 |
| 5 | 75,435 | 24,565 | 0.245650 | 0.294075 |
| 6 | 75,147 | 24,853 | 0.248530 | 0.296214 |
| 7 | 75,307 | 24,693 | 0.246930 | 0.294091 |
| 8 | 75,286 | 24,714 | 0.247140 | 0.293163 |
| 9 | 75,178 | 24,822 | 0.248220 | 0.294545 |

## Reproduce

From the project folder:

```bash
.venv/bin/python run_experiment.py
```

[Complete results and source hashes](../results/greedy_experiment.json) contain every run's settings, counts, metrics, summaries, and paired comparisons. Python used: 3.14.0.

Model assumptions: [model.md](model.md). The source hashes identify the exact simulation, workload generator, experiment script, and model specification.

The M6 measurements were collected before the policy refactor. The
[original source snapshot](../results/greedy_source.json) preserves the files
matching their recorded hashes. The M7 comparison reproduced all ten M6
greedy baseline results exactly after the refactor.
