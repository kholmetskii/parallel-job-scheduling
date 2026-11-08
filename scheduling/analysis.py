"""Summarize runs and compare policies, measurement lengths, or server counts."""

import math
from statistics import mean, stdev

from scheduling.experiments import BASELINE


METRICS = ("blocking_probability", "mean_execution_time")


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


def compare_runs(runs: list[dict], baseline: tuple[int, int]) -> list[dict]:
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


def summarize_server_runs(runs: list[dict]) -> list[dict]:
    """Keep system sizes separate and require matching seeds and run lengths."""
    if not runs:
        raise ValueError("At least two runs per server count are required")
    configurations = {(row["warmup_arrivals"], row["measured_arrivals"]) for row in runs}
    if len(configurations) != 1:
        raise ValueError("All server counts must use the same warm-up and measured counts")
    summaries = []
    reference_seeds = None
    for servers in sorted({row["servers"] for row in runs}):
        group = [row for row in runs if row["servers"] == servers]
        rates = {row["arrival_rate"] for row in group}
        if len(rates) != 1:
            raise ValueError("Each server count must use one arrival rate")
        seeds = {row["seed"] for row in group}
        if reference_seeds is not None and seeds != reference_seeds:
            raise ValueError("All server counts must use matching workload seeds")
        reference_seeds = seeds
        summary, = summarize_runs(group)
        summaries.append({"servers": servers,
                          "arrival_rate": rates.pop(),
                          **summary})
    return summaries
