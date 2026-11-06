"""Compare greedy and paper-randomized allocation on matched workloads."""

import hashlib
import json
import platform
import struct
from pathlib import Path
from statistics import mean, stdev

from policies import GreedyPolicy, RandomizedPolicy
from run_experiment import (
    ARRIVAL_RATE, BASELINE, CONFIGURATIONS, MEAN_JOB_SIZE, METRICS, SEEDS,
    SERVERS, TOLERANCES, compare_runs, sensitivity_within_tolerance, summarize_runs,
)
from simulation import SPEEDUPS, Simulator
from workload import WorkloadGenerator


POLICY_SEED_OFFSET = 10_000


def workload_digest(arrivals: list[tuple[float, float]]) -> str:
    digest = hashlib.sha256()
    for arrival_time, size in arrivals:
        digest.update(struct.pack("<dd", arrival_time, size))
    return digest.hexdigest()


def run_policy(
    arrivals: list[tuple[float, float]],
    seed: int,
    policy: str,
    warmup_arrivals: int,
    policy_seed: int | None = None,
) -> dict:
    """Run one policy and retain scalar results and an input fingerprint."""
    if type(warmup_arrivals) is not int or not 0 <= warmup_arrivals < len(arrivals):
        raise ValueError("warmup_arrivals must leave at least one measured arrival")
    if policy == "greedy":
        allocation_policy = GreedyPolicy(max_servers=len(SPEEDUPS))
        policy_seed = None
    elif policy == "randomized":
        if type(policy_seed) is not int:
            raise ValueError("A reproducible comparison requires an integer policy_seed")
        allocation_policy = RandomizedPolicy(seed=policy_seed)
    else:
        raise ValueError("Unknown allocation policy")
    result = Simulator(servers=SERVERS, policy=allocation_policy).run(
        arrivals, warmup_arrivals=warmup_arrivals)
    statistics = result["statistics"]
    allocations = {str(count): 0 for count in range(1, len(SPEEDUPS) + 1)}
    for event in result["events"]:
        if event["event"] == "accepted" and event["job_id"] > warmup_arrivals:
            allocations[str(event["allocated_servers"])] += 1
    measured = len(arrivals) - warmup_arrivals
    if (statistics["arrivals"] != measured
            or sum(allocations.values()) != statistics["accepted"]
            or result["accepted"] != result["completed"]
            or result["final_idle_servers"] != SERVERS):
        raise RuntimeError("Policy comparison finished with inconsistent counts")
    return {
        "policy": policy, "seed": seed, "policy_seed": policy_seed,
        "workload_sha256": workload_digest(arrivals),
        "servers": SERVERS, "arrival_rate": ARRIVAL_RATE, "mean_job_size": MEAN_JOB_SIZE,
        "speedups": list(SPEEDUPS), "max_servers_per_job": len(SPEEDUPS),
        "warmup_arrivals": warmup_arrivals, "measured_arrivals": measured,
        "total_arrivals": result["arrivals"], "total_accepted": result["accepted"],
        "total_rejected": result["rejected"], "total_completed": result["completed"],
        "final_idle_servers": result["final_idle_servers"],
        "measured_accepted": statistics["accepted"], "measured_rejected": statistics["rejected"],
        "measured_allocations": allocations,
        "measured_total_execution_time": statistics["total_execution_time"],
        "blocking_probability": statistics["blocking_probability"],
        "mean_execution_time": statistics["mean_execution_time"],
    }


def policy_differences(runs: list[dict], baseline: tuple[int, int] = BASELINE) -> dict:
    """Calculate randomized-minus-greedy differences for identical inputs."""
    groups = {"greedy": {}, "randomized": {}}
    for run in runs:
        if (run["warmup_arrivals"], run["measured_arrivals"]) != baseline:
            continue
        group = groups[run["policy"]]
        if run["seed"] in group:
            raise ValueError("Duplicate policy/workload seed at the baseline")
        group[run["seed"]] = run
    greedy, randomized = groups["greedy"], groups["randomized"]
    if len(greedy) < 2 or greedy.keys() != randomized.keys():
        raise ValueError("The policies require at least two matching workload seeds")
    pairs = []
    for seed in sorted(greedy):
        if greedy[seed]["workload_sha256"] != randomized[seed]["workload_sha256"]:
            raise ValueError("Paired policies must receive identical arrivals and job sizes")
        pair = {"seed": seed, "policy_seed": randomized[seed]["policy_seed"]}
        for metric in METRICS:
            pair[f"{metric}_delta"] = randomized[seed][metric] - greedy[seed][metric]
        pairs.append(pair)
    summary = {"pairs": len(pairs)}
    for metric in METRICS:
        values = [pair[f"{metric}_delta"] for pair in pairs]
        summary[f"{metric}_mean_delta"] = mean(values)
        summary[f"{metric}_delta_sd"] = stdev(values)
    return {"per_seed": pairs, "summary": summary}


def build_report(experiment: dict) -> str:
    baseline = {row["policy"]: row for row in experiment["summaries"]
                if (row["warmup_arrivals"], row["measured_arrivals"]) == BASELINE}
    greedy, randomized = baseline["greedy"], baseline["randomized"]
    difference = experiment["paired_policy_differences"]["summary"]
    blocking_delta = difference["blocking_probability_mean_delta"]
    time_delta = difference["mean_execution_time_mean_delta"]
    within = experiment["randomized_sensitivity_within_tolerance"]
    lines = [
        "# M7: Greedy versus the paper's randomized policy", "",
        f"At 100 servers, greedy blocked **{greedy['blocking_probability_mean']:.3%}** "
        f"of arrivals and randomized blocked **{randomized['blocking_probability_mean']:.3%}**. "
        f"Mean accepted-job execution time was **{greedy['mean_execution_time_mean']:.6f}** "
        f"and **{randomized['mean_execution_time_mean']:.6f}** time units, respectively.", "",
        "## Policy and experiment", "",
        "- Greedy targets 5 servers. The paper's greedy(p*) targets 3 with probability "
        "0.625 and 4 with probability 0.375. Both allocate the smaller of target and idle capacity, "
        "reject only when no server is idle, and keep allocations until completion.",
        "- These probabilities apply to normalized rate 0.8, mean inherent job size 1, "
        "and speedups (1, 1.8, 2.5, 3, 3.4). From the paper's optimal state, "
        "y3=0.2 and y4=0.1: p3=2.5*0.2/0.8=0.625 and p4=3*0.1/0.8=0.375.",
        "- 100 servers, Poisson arrival rate 80, exponential inherent job sizes with mean 1.",
        "- Baseline: 10,000 warm-up arrivals and 100,000 measured arrivals per workload seed.",
        "- Workload seeds 0-9. Each pair uses exactly the same arrival times and sizes; "
        "matching SHA256 fingerprints are checked before computing paired differences.",
        "- Policy seeds are 10,000 plus the workload seed. Policy randomness has its own "
        "generator. A target is drawn for every arrival, including warm-up and blocked jobs.",
        "- Every run starts from an empty system with a fresh policy stream. Warm-up "
        "allocations remain active, and measured accepted jobs contribute their full durations.",
        "- Server and job conservation checks remain enabled. All accepted jobs finish.", "",
        "## Baseline comparison", "",
        "Means weight the ten runs equally. SD is sample standard deviation across runs, "
        "not a confidence interval.", "",
        "| Policy | Runs | Blocking mean | Blocking SD | Execution mean | Execution SD |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ("greedy", "randomized"):
        row = baseline[name]
        lines.append(f"| {name} | {row['runs']} | {row['blocking_probability_mean']:.6f} | "
                     f"{row['blocking_probability_sd']:.6f} | {row['mean_execution_time_mean']:.6f} | "
                     f"{row['mean_execution_time_sd']:.6f} |")
    lines += ["", "## Paired policy differences", "",
              "Each difference is randomized minus greedy on the same workload. "
              "The SD describes variation in these matched differences across seeds.", "",
              "| Metric | Mean difference | Difference SD |",
              "| --- | ---: | ---: |",
              f"| Blocking probability | {blocking_delta:+.6f} | {difference['blocking_probability_delta_sd']:.6f} |",
              f"| Mean execution time | {time_delta:+.6f} | {difference['mean_execution_time_delta_sd']:.6f} |", "",
              f"Blocking changed by {blocking_delta * 100:+.3f} percentage points "
              f"({blocking_delta / greedy['blocking_probability_mean']:+.2%} relative to greedy). "
              f"Accepted-job execution time changed by {time_delta:+.6f} time units "
              f"({time_delta / greedy['mean_execution_time_mean']:+.2%} relative).", "",
              "## Randomized policy sensitivity", "",
              "The new policy receives its own warm-up and run-length checks. "
              "The same six configurations and ten seeds as M6 are used. "
              "The baseline randomized runs are shared with the main policy comparison.", "",
              "| Warm-up | Measured | Runs | Blocking mean | Blocking SD | Execution mean | Execution SD |",
              "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in experiment["summaries"]:
        if row["policy"] == "randomized":
            lines.append(f"| {row['warmup_arrivals']:,} | {row['measured_arrivals']:,} | {row['runs']} | "
                         f"{row['blocking_probability_mean']:.6f} | {row['blocking_probability_sd']:.6f} | "
                         f"{row['mean_execution_time_mean']:.6f} | {row['mean_execution_time_sd']:.6f} |")
    lines += ["", "The following deltas compare randomized configurations with the randomized baseline, "
              "pairing the same workload and policy seeds.", "",
              "| Warm-up | Measured | Blocking mean delta | Blocking delta SD | Execution mean delta | Execution delta SD |",
              "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in experiment["randomized_sensitivity"]:
        lines.append(f"| {row['warmup_arrivals']:,} | {row['measured_arrivals']:,} | "
                     f"{row['blocking_probability_mean_delta']:+.6f} | {row['blocking_probability_delta_sd']:.6f} | "
                     f"{row['mean_execution_time_mean_delta']:+.6f} | {row['mean_execution_time_delta_sd']:.6f} |")
    lines += ["",
              "As in M6, the exploratory tolerances are 0.002 probability "
              "(0.2 percentage points) and 0.002 time units for changes in configuration means. "
              "They are practical thresholds, not significance tests. Checks cover shorter "
              "warm-ups at a fixed measured length and doubling the measured length.", "",
              ("The checked changes are within these tolerances, supporting the same initial "
               "measurement settings for both policies." if within else
               "At least one check exceeds tolerance; extend the settings before adopting the comparison."), "",
              "## Interpretation and scope", "",
              "The comparison measures the tradeoff between admission and accepted-job speed. "
              "Rejected jobs contribute to blocking but have no execution-time observation. "
              "The two policies can accept different subsets of the shared workload.", "",
              "For these parameters the paper's large-system execution benchmark is "
              "0.625/2.5 + 0.375/3 = 0.375 time units, with blocking tending to zero as "
              "server count grows. Partial allocations can lengthen executions at finite size. "
              "This experiment uses n=100 and does not establish asymptotic optimality "
              "or guarantee zero blocking. More seeds or longer runs may be needed for tighter precision.", "",
              "Reference: Mukhopadhyay et al., *On Optimal Server Allocation for a Loss System "
              "With Moldable Jobs*, Sections IV and VII. "
              "[DOI](https://doi.org/10.1109/TON.2025.3598595).", "",
              "## Reproduce", "", "```bash", ".venv/bin/python run_comparison.py", "```", "",
              "[Complete results](../results/policy_comparison.json) include every run, "
              "workload fingerprints, both seeds, allocation counts, summaries, and paired differences. "
              "The source text and SHA256 hashes are embedded for reproducibility. "
              f"Python used: {experiment['python_version']}.", "",
              "Optional figure (after installing requirements-plot.txt):", "",
              "```bash", ".venv/bin/python plot_comparison.py", "```", "",
              "![Policy comparison](../results/figures/policy_comparison.png)", ""]
    return "\n".join(lines)


def main() -> None:
    runs = []
    total = (len(CONFIGURATIONS) + 1) * len(SEEDS)
    for seed in SEEDS:
        arrivals = WorkloadGenerator(ARRIVAL_RATE, MEAN_JOB_SIZE, seed=seed).generate(
            max(warmup + measured for warmup, measured in CONFIGURATIONS))
        for warmup, measured in CONFIGURATIONS:
            jobs = arrivals[:warmup + measured]
            names = ("greedy", "randomized") if (warmup, measured) == BASELINE else ("randomized",)
            for name in names:
                row = run_policy(jobs, seed, name, warmup,
                                 policy_seed=POLICY_SEED_OFFSET + seed if name == "randomized" else None)
                runs.append(row)
                print(f"Run {len(runs)}/{total}: {name}, seed={seed}, warm-up={warmup}, "
                      f"measured={measured}; blocking={row['blocking_probability']:.6f}, "
                      f"mean execution={row['mean_execution_time']:.6f}", flush=True)
    random_runs = [row for row in runs if row["policy"] == "randomized"]
    summaries = []
    for name in ("greedy", "randomized"):
        for summary in summarize_runs([row for row in runs if row["policy"] == name]):
            summaries.append({"policy": name, **summary})
    comparisons = compare_runs(random_runs)
    project = Path(__file__).resolve().parent
    source_text = {name: (project / name).read_text(encoding="utf-8")
                   for name in ("simulation.py", "policies.py", "workload.py",
                                "run_experiment.py", "run_comparison.py", "docs/model.md")}
    experiment = {
        "python_version": platform.python_version(), "source_text": source_text,
        "source_sha256": {name: hashlib.sha256(text.encode('utf-8')).hexdigest()
                          for name, text in source_text.items()},
        "workload_seeds": list(SEEDS), "policy_seed_offset": POLICY_SEED_OFFSET,
        "baseline": {"warmup_arrivals": BASELINE[0], "measured_arrivals": BASELINE[1]},
        "target_probabilities": {"3": 0.625, "4": 0.375},
        "large_system_execution_benchmark": 0.375,
        "sensitivity_tolerances": TOLERANCES,
        "randomized_sensitivity_within_tolerance": sensitivity_within_tolerance(comparisons),
        "runs": runs, "summaries": summaries,
        "paired_policy_differences": policy_differences(runs),
        "randomized_sensitivity": comparisons,
    }
    output = project / "results" / "policy_comparison.json"
    report = project / "docs" / "policy_comparison.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(experiment, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report.write_text(build_report(experiment), encoding="utf-8")
    print("Saved results/policy_comparison.json and docs/policy_comparison.md")
    if not experiment["randomized_sensitivity_within_tolerance"]:
        print("Review randomized-policy sensitivity before adopting the comparison.")


if __name__ == "__main__":
    main()
