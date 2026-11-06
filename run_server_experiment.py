"""Compare RandomizedPolicy across server counts at fixed load per server."""

import hashlib
import json
import platform
import struct
from pathlib import Path

from policies import RandomizedPolicy
from run_experiment import BASELINE, SEEDS, summarize_runs
from simulation import SPEEDUPS, Simulator
from workload import WorkloadGenerator


SERVER_COUNTS = (25, 50, 100, 200, 500, 1_000)
NORMALIZED_LOAD = 0.8
MEAN_JOB_SIZE = 1.0
POLICY_SEED_OFFSET = 10_000


def run_trial(
    servers: int,
    seed: int,
    warmup_arrivals: int = BASELINE[0],
    measured_arrivals: int = BASELINE[1],
) -> dict:
    """Run a fresh system with arrival_rate * mean_job_size / servers = 0.8."""
    if type(servers) is not int or servers < 1:
        raise ValueError("servers must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer for reproducible experiments")
    if type(warmup_arrivals) is not int or warmup_arrivals < 0:
        raise ValueError("warmup_arrivals must be a nonnegative integer")
    if type(measured_arrivals) is not int or measured_arrivals < 1:
        raise ValueError("measured_arrivals must be a positive integer")
    arrival_rate = NORMALIZED_LOAD * servers / MEAN_JOB_SIZE
    policy_seed = POLICY_SEED_OFFSET + seed
    arrivals = WorkloadGenerator(arrival_rate, MEAN_JOB_SIZE, seed=seed).generate(
        warmup_arrivals + measured_arrivals)
    digest = hashlib.sha256()
    for arrival_time, size in arrivals:
        digest.update(struct.pack("<dd", arrival_time, size))
    result = Simulator(servers=servers, policy=RandomizedPolicy(seed=policy_seed)).run(
        arrivals, warmup_arrivals=warmup_arrivals)
    statistics = result["statistics"]
    allocations = {str(count): 0 for count in range(1, len(SPEEDUPS) + 1)}
    for event in result["events"]:
        if event["event"] == "accepted" and event["job_id"] > warmup_arrivals:
            allocations[str(event["allocated_servers"])] += 1
    if (result["arrivals"] != warmup_arrivals + measured_arrivals
            or statistics["arrivals"] != measured_arrivals
            or statistics["accepted"] + statistics["rejected"] != measured_arrivals
            or sum(allocations.values()) != statistics["accepted"]
            or result["accepted"] != result["completed"]
            or result["final_idle_servers"] != servers):
        raise RuntimeError("The server-count experiment finished with inconsistent counts")
    return {
        "policy": "randomized", "servers": servers,
        "seed": seed, "policy_seed": policy_seed,
        "arrival_rate": arrival_rate, "normalized_load": NORMALIZED_LOAD,
        "mean_job_size": MEAN_JOB_SIZE, "speedups": list(SPEEDUPS),
        "max_servers_per_job": len(SPEEDUPS),
        "workload_sha256": digest.hexdigest(),
        "warmup_arrivals": warmup_arrivals, "measured_arrivals": measured_arrivals,
        "total_arrivals": result["arrivals"], "total_accepted": result["accepted"],
        "total_rejected": result["rejected"], "total_completed": result["completed"],
        "final_idle_servers": result["final_idle_servers"],
        "measured_accepted": statistics["accepted"], "measured_rejected": statistics["rejected"],
        "measured_allocations": allocations,
        "measured_total_execution_time": statistics["total_execution_time"],
        "blocking_probability": statistics["blocking_probability"],
        "mean_execution_time": statistics["mean_execution_time"],
    }


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
        seeds = {row["seed"] for row in group}
        if reference_seeds is not None and seeds != reference_seeds:
            raise ValueError("All server counts must use matching workload seeds")
        reference_seeds = seeds
        summary, = summarize_runs(group)
        summaries.append({"servers": servers,
                          "arrival_rate": NORMALIZED_LOAD * servers / MEAN_JOB_SIZE,
                          **summary})
    return summaries


def build_report(experiment: dict) -> str:
    first, last = experiment["summaries"][0], experiment["summaries"][-1]
    settings = experiment["measurement"]
    lines = [
        "# Randomized policy: different server counts", "",
        "Compare system sizes while keeping the offered load per server constant.", "",
        f"From {first['servers']} to {last['servers']:,} servers, blocking changes from "
        f"**{first['blocking_probability_mean']:.3%}** to "
        f"**{last['blocking_probability_mean']:.3%}**. Mean accepted-job execution time "
        f"changes from **{first['mean_execution_time_mean']:.6f}** to "
        f"**{last['mean_execution_time_mean']:.6f}** time units.", "",
        "## Settings", "",
        "- RandomizedPolicy targets 3 servers with probability 0.625 and 4 with probability "
        "0.375; allocate the smaller of target and idle capacity.",
        "- Arrival rate is 0.8 times the server count. Mean exponential job size stays at 1. "
        "The normalized load, arrival_rate * mean_job_size / servers, stays at 0.8. "
        "This is offered load, not measured utilization. The policy probabilities remain applicable.",
        "- Speedups stay at (1, 1.8, 2.5, 3, 3.4); each job still has a maximum of 5 servers.",
        f"- Each size uses {len(experiment['workload_seeds'])} workload seeds, "
        f"{settings['warmup_arrivals']:,} warm-up arrivals and "
        f"{settings['measured_arrivals']:,} measured arrivals per seed.",
        "- Reuse workload seeds 0-9 and separate policy seeds 10000-10009 across sizes. "
        "This shares random draws and job sizes; arrival timestamps change with arrival rate. "
        "Different seeds give independent replications; sizes sharing a seed are correlated.",
        "- Start each run empty, retain active warm-up jobs at the measurement cutoff, "
        "and drain all accepted jobs after the final arrival. Conservation checks remain enabled.", "",
        "## Results", "",
        "Means weight the ten runs equally. SD is sample standard deviation across seeds, "
        "not a confidence interval. Execution times include accepted jobs only.", "",
        "| Servers | Arrival rate | Blocking mean | Blocking SD | Execution mean | Execution SD |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in experiment["summaries"]:
        lines.append(f"| {row['servers']:,} | {row['arrival_rate']:g} | "
                     f"{row['blocking_probability_mean']:.3%} | "
                     f"{row['blocking_probability_sd']:.6f} | "
                     f"{row['mean_execution_time_mean']:.6f} | "
                     f"{row['mean_execution_time_sd']:.6f} |")
    lines += ["", "![Randomized policy across server counts](../results/figures/randomized_servers.png)", "",
              "## Interpretation", "",
              "Increasing the arrival rate with capacity asks whether a larger system performs "
              "differently at the same offered load per server. Keeping arrival rate fixed would "
              "instead make larger systems progressively less loaded.", "",
              f"The paper's large-system execution benchmark for these parameters is "
              f"{experiment['large_system_execution_benchmark']:.3f} time units, with blocking "
              "tending to zero as server count grows. Finite simulations can illustrate the "
              "trend but cannot prove that limit. Partial allocations can increase execution "
              "time, and different sizes can accept different subsets of jobs.", "",
              "The warm-up and measurement counts come from the 100-server experiment. "
              "They have not been separately validated at every size. Because arrival rate "
              "increases, the same arrival count spans less simulated time in larger systems; "
              "treat this as an exploratory comparison.", "",
              "Reference: Mukhopadhyay et al., *On Optimal Server Allocation for a Loss System "
              "With Moldable Jobs*. [DOI](https://doi.org/10.1109/TON.2025.3598595).", "",
              "## Reproduce", "", "```bash", ".venv/bin/python run_server_experiment.py", "",
              "# Optional figure; install requirements-plot.txt first.",
              ".venv/bin/python plot_server_experiment.py", "```", "",
              "[Complete results](../results/randomized_servers.json) contain each run, settings, "
              "both seeds, allocation counts, workload fingerprints, summaries and source snapshots. "
              f"Python used: {experiment['python_version']}.", ""]
    return "\n".join(lines)


def main() -> None:
    runs = []
    for servers in SERVER_COUNTS:
        for seed in SEEDS:
            row = run_trial(servers, seed)
            runs.append(row)
            print(f"Run {len(runs)}/{len(SERVER_COUNTS) * len(SEEDS)}: "
                  f"servers={servers}, seed={seed}; blocking={row['blocking_probability']:.6f}, "
                  f"mean execution={row['mean_execution_time']:.6f}", flush=True)
    project = Path(__file__).resolve().parent
    source_text = {name: (project / name).read_text(encoding="utf-8")
                   for name in ("simulation.py", "policies.py", "workload.py",
                                "run_experiment.py", "run_server_experiment.py", "docs/model.md")}
    probability_three = RandomizedPolicy(seed=0).probability_three
    experiment = {
        "python_version": platform.python_version(), "source_text": source_text,
        "source_sha256": {name: hashlib.sha256(text.encode("utf-8")).hexdigest()
                          for name, text in source_text.items()},
        "server_counts": list(SERVER_COUNTS), "normalized_load": NORMALIZED_LOAD,
        "mean_job_size": MEAN_JOB_SIZE, "workload_seeds": list(SEEDS),
        "policy_seed_offset": POLICY_SEED_OFFSET,
        "measurement": {"warmup_arrivals": BASELINE[0], "measured_arrivals": BASELINE[1]},
        "target_probabilities": {"3": probability_three, "4": 1 - probability_three},
        "large_system_execution_benchmark": MEAN_JOB_SIZE * (
            probability_three / SPEEDUPS[2] + (1 - probability_three) / SPEEDUPS[3]),
        "runs": runs, "summaries": summarize_server_runs(runs),
    }
    output = project / "results" / "randomized_servers.json"
    report = project / "docs" / "server_experiment.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(experiment, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report.write_text(build_report(experiment), encoding="utf-8")
    print("Saved results/randomized_servers.json and docs/server_experiment.md")


if __name__ == "__main__":
    main()
