"""Run and document the M6 greedy baseline and sensitivity checks."""

import hashlib
import json
import math
import platform
from pathlib import Path
from statistics import mean, stdev

from simulation import SPEEDUPS, Simulator
from workload import WorkloadGenerator


SERVERS = 100
ARRIVAL_RATE = 0.8 * SERVERS
MEAN_JOB_SIZE = 1.0
SEEDS = tuple(range(10))
BASELINE = (10_000, 100_000)
CONFIGURATIONS = (
    (1_000, 100_000),
    (5_000, 100_000),
    BASELINE,
    (10_000, 10_000),
    (10_000, 50_000),
    (10_000, 200_000),
)
METRICS = ("blocking_probability", "mean_execution_time")
# Exploratory resolution for comparing configuration means, not significance tests.
TOLERANCES = {"blocking_probability": 0.002, "mean_execution_time": 0.002}


def run_trial(seed: int, warmup_arrivals: int, measured_arrivals: int) -> dict:
    """Run one fresh workload and retain settings and scalar results."""
    if type(warmup_arrivals) is not int or warmup_arrivals < 0:
        raise ValueError("warmup_arrivals must be a nonnegative integer")
    if type(measured_arrivals) is not int or measured_arrivals < 1:
        raise ValueError("measured_arrivals must be a positive integer")
    total_arrivals = warmup_arrivals + measured_arrivals
    workload = WorkloadGenerator(ARRIVAL_RATE, MEAN_JOB_SIZE, seed=seed)
    arrivals = workload.generate(total_arrivals)
    result = Simulator(servers=SERVERS).run(arrivals, warmup_arrivals=warmup_arrivals)
    statistics = result["statistics"]
    if (result["arrivals"] != total_arrivals
            or statistics["arrivals"] != measured_arrivals
            or result["accepted"] != result["completed"]
            or result["final_idle_servers"] != SERVERS):
        raise RuntimeError("The experiment finished with inconsistent counts")
    return {
        "policy": "greedy",
        "seed": seed,
        "servers": SERVERS,
        "arrival_rate": ARRIVAL_RATE,
        "mean_job_size": MEAN_JOB_SIZE,
        "max_servers_per_job": len(SPEEDUPS),
        "speedups": list(SPEEDUPS),
        "warmup_arrivals": warmup_arrivals,
        "measured_arrivals": measured_arrivals,
        "total_arrivals": result["arrivals"],
        "total_accepted": result["accepted"],
        "total_rejected": result["rejected"],
        "total_completed": result["completed"],
        "final_idle_servers": result["final_idle_servers"],
        "measured_accepted": statistics["accepted"],
        "measured_rejected": statistics["rejected"],
        "measured_total_execution_time": statistics["total_execution_time"],
        "blocking_probability": statistics["blocking_probability"],
        "mean_execution_time": statistics["mean_execution_time"],
    }


def group_runs(runs: list[dict]) -> dict[tuple[int, int], dict[int, dict]]:
    """Group by configuration and seed, rejecting duplicate observations."""
    groups = {}
    for run in runs:
        key = (run["warmup_arrivals"], run["measured_arrivals"])
        group = groups.setdefault(key, {})
        if run["seed"] in group:
            raise ValueError("Duplicate seed within an experiment configuration")
        for metric in METRICS:
            value = run[metric]
            if value is None or not math.isfinite(value):
                raise ValueError(f"Cannot summarize an unavailable or nonfinite {metric}")
        group[run["seed"]] = run
    return groups


def summarize_runs(runs: list[dict]) -> list[dict]:
    """Calculate equally weighted run means and sample SDs across seeds."""
    summaries = []
    for (warmup, measured), group in sorted(group_runs(runs).items()):
        if len(group) < 2:
            raise ValueError("At least two seeds are needed for a sample standard deviation")
        summary = {"warmup_arrivals": warmup, "measured_arrivals": measured,
                   "runs": len(group)}
        for metric in METRICS:
            values = [run[metric] for run in group.values()]
            summary[f"{metric}_mean"] = mean(values)
            summary[f"{metric}_sd"] = stdev(values)
        summaries.append(summary)
    return summaries


def compare_runs(runs: list[dict], baseline: tuple[int, int] = BASELINE) -> list[dict]:
    """Compare matched seeds because configurations share workload prefixes."""
    groups = group_runs(runs)
    reference = groups[baseline]
    if len(reference) < 2:
        raise ValueError("At least two matched seeds are needed for paired comparisons")
    comparisons = []
    for (warmup, measured), group in sorted(groups.items()):
        if (warmup, measured) == baseline:
            continue
        if group.keys() != reference.keys():
            raise ValueError("Configurations must contain the same seeds for paired comparisons")
        comparison = {"warmup_arrivals": warmup, "measured_arrivals": measured}
        for metric in METRICS:
            differences = [group[seed][metric] - reference[seed][metric]
                           for seed in sorted(reference)]
            comparison[f"{metric}_mean_delta"] = mean(differences)
            comparison[f"{metric}_delta_sd"] = stdev(differences)
        comparisons.append(comparison)
    return comparisons


def sensitivity_within_tolerance(comparisons: list[dict]) -> bool:
    """Check shorter warm-ups and a doubled measured run against the baseline."""
    checks = {(1_000, 100_000), (5_000, 100_000), (10_000, 200_000)}
    selected = [row for row in comparisons
                if (row["warmup_arrivals"], row["measured_arrivals"]) in checks]
    return len(selected) == len(checks) and all(
        abs(row[f"{metric}_mean_delta"]) <= TOLERANCES[metric]
        for row in selected for metric in METRICS
    )


def build_report(experiment: dict) -> str:
    """Build a report directly from the saved measurements and summaries."""
    summaries = experiment["summaries"]
    baseline = next(row for row in summaries
                    if (row["warmup_arrivals"], row["measured_arrivals"]) == BASELINE)
    within = experiment["sensitivity_within_tolerance"]
    conclusion = (
        "The checked mean changes are within the exploratory tolerances. "
        "Use 10,000 warm-up arrivals and 100,000 measured arrivals as the first greedy baseline."
        if within else
        "At least one sensitivity check exceeds the exploratory tolerance. "
        "Extend the warm-up or measured run before adopting this baseline."
    )
    lines = [
        "# M6: 100-server greedy experiment", "",
        f"Across {len(SEEDS)} seeds, baseline blocking probability is "
        f"**{baseline['blocking_probability_mean']:.6f}** "
        f"({baseline['blocking_probability_mean']:.2%}); mean execution time is "
        f"**{baseline['mean_execution_time_mean']:.6f}** time units.", "",
        "## Settings and method", "",
        "- Policy: greedy allocation, at most 5 servers per job; no waiting queue.",
        "- Servers: 100; Poisson arrival rate: 80; exponential mean job size: 1.",
        "- Speedups for 1–5 servers: 1, 1.8, 2.5, 3, 3.4.",
        "- Seeds: 0–9, with a fresh workload generator and simulator for each run.",
        "- Baseline: 10,000 warm-up arrivals, followed by 100,000 measured arrivals.",
        "- Warm-up jobs keep their allocations but contribute no measurements. "
        "Measured accepted jobs contribute their full execution times.",
        "- Every run retains server/job conservation checks and finishes all accepted jobs.",
        "- Table means weight the ten run estimates equally. SD is the sample standard "
        "deviation across seeds, describing run-to-run variation; it is not a confidence interval.", "",
        "## Results by configuration", "",
        "| Warm-up arrivals | Measured arrivals | Runs | Blocking mean | Blocking SD | Execution mean | Execution SD |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summaries:
        lines.append(
            f"| {row['warmup_arrivals']:,} | {row['measured_arrivals']:,} | {row['runs']} | "
            f"{row['blocking_probability_mean']:.6f} | {row['blocking_probability_sd']:.6f} | "
            f"{row['mean_execution_time_mean']:.6f} | {row['mean_execution_time_sd']:.6f} |")
    lines += ["", "## Sensitivity checks", "",
              "Exploratory tolerances were set before running: 0.002 for the change in mean "
              "blocking probability (0.2 percentage points) and 0.002 time units for the "
              "change in mean execution time. These are practical comparison thresholds, "
              "not statistical significance tests.", "",
              "The same seed produces a shared workload prefix across configurations. "
              "The table therefore pairs matching seeds. Delta means configuration minus "
              "baseline; delta SD describes variation in those paired differences.", "",
              "| Warm-up | Measured | Blocking mean delta | Blocking delta SD | Execution mean delta | Execution delta SD |",
              "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in experiment["comparisons"]:
        lines.append(
            f"| {row['warmup_arrivals']:,} | {row['measured_arrivals']:,} | "
            f"{row['blocking_probability_mean_delta']:+.6f} | {row['blocking_probability_delta_sd']:.6f} | "
            f"{row['mean_execution_time_mean_delta']:+.6f} | {row['mean_execution_time_delta_sd']:.6f} |")
    lines += ["", conclusion, "",
              "The checks compare warm-ups of 1,000 and 5,000 with 10,000 at a fixed "
              "100,000 measured arrivals, and compare 100,000 with 200,000 measured arrivals "
              "at a fixed 10,000 warm-up. Shorter 10,000- and 50,000-arrival runs also show "
              "how run-to-run variation changes with run length.", "",
              "These finite checks support an initial baseline; they do not prove that "
              "all initialization bias has disappeared. Results apply to this model and "
              "parameter set. Further experiments may require greater precision.", "",
              "## Baseline runs", "",
              "| Seed | Measured accepted | Measured rejected | Blocking probability | Mean execution time |",
              "| ---: | ---: | ---: | ---: | ---: |"]
    for row in experiment["runs"]:
        if (row["warmup_arrivals"], row["measured_arrivals"]) == BASELINE:
            lines.append(f"| {row['seed']} | {row['measured_accepted']:,} | "
                         f"{row['measured_rejected']:,} | {row['blocking_probability']:.6f} | "
                         f"{row['mean_execution_time']:.6f} |")
    lines += ["", "## Reproduce", "", "From the project folder:", "",
              "```bash", ".venv/bin/python run_experiment.py", "```", "",
              "[Complete results and source hashes](../results/greedy_experiment.json) "
              "contain every run's settings, counts, metrics, summaries, and paired comparisons. "
              f"Python used: {experiment['python_version']}.", "",
              "Model assumptions: [model.md](model.md). The source hashes identify the "
              "exact code and model specification. "
              "[Source snapshot](../results/greedy_source.json) preserves those files.", ""]
    return "\n".join(lines)


def main() -> None:
    runs = []
    total = len(CONFIGURATIONS) * len(SEEDS)
    for warmup, measured in CONFIGURATIONS:
        for seed in SEEDS:
            run = run_trial(seed, warmup, measured)
            runs.append(run)
            print(f"Run {len(runs)}/{total}: warm-up={warmup}, measured={measured}, seed={seed}; "
                  f"blocking={run['blocking_probability']:.6f}, "
                  f"mean execution={run['mean_execution_time']:.6f}", flush=True)

    project = Path(__file__).resolve().parent
    comparisons = compare_runs(runs)
    source_text = {name: (project / name).read_text(encoding="utf-8")
                   for name in ("simulation.py", "policies.py", "workload.py",
                                "run_experiment.py", "docs/model.md")}
    experiment = {
        "python_version": platform.python_version(),
        "source_sha256": {
            name: hashlib.sha256((project / name).read_bytes()).hexdigest()
            for name in source_text
        },
        "seeds": list(SEEDS),
        "baseline": {"warmup_arrivals": BASELINE[0], "measured_arrivals": BASELINE[1]},
        "sensitivity_tolerances": TOLERANCES,
        "sensitivity_within_tolerance": sensitivity_within_tolerance(comparisons),
        "runs": runs,
        "summaries": summarize_runs(runs),
        "comparisons": comparisons,
    }
    output = project / "results" / "greedy_experiment.json"
    report = project / "docs" / "experiment_results.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(experiment, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    snapshot = {"source_sha256": experiment["source_sha256"], "source_text": source_text}
    (output.parent / "greedy_source.json").write_text(
        json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    report.write_text(build_report(experiment), encoding="utf-8")
    print("Saved results/greedy_experiment.json and docs/experiment_results.md")
    if not experiment["sensitivity_within_tolerance"]:
        print("Review the sensitivity checks before adopting the baseline.")


if __name__ == "__main__":
    main()
