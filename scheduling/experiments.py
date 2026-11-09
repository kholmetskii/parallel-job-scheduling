"""Run policies on generated or supplied workloads without writing files."""

import hashlib
import struct

from scheduling.config import ExperimentSettings, ModelSettings
from scheduling.job import Job
from scheduling.policies import GreedyPolicy, RandomizedPolicy
from scheduling.simulator import Simulator
from scheduling.workload import WorkloadGenerator


BASELINE = (10_000, 100_000)


def workload_digest(arrivals: list[Job]) -> str:
    """Fingerprint job IDs, arrival times, and sizes."""
    digest = hashlib.sha256()
    for job in arrivals:
        digest.update(str(job.id).encode("ascii") + b"\0")
        digest.update(struct.pack("<dd", job.arrival_time, job.size))
    return digest.hexdigest()


def run_policy(
    arrivals: list[Job],
    seed: int,
    policy: str,
    warmup_arrivals: int,
    policy_seed: int | None = None,
    model: ModelSettings | None = None,
    record_events: bool = True,
) -> dict:
    """Run one policy and return measurements and the workload fingerprint.

    RandomizedPolicy retains its baseline calibration until target calculation
    is implemented. Supplied model settings also determine the actual speedups.
    Measurements do not depend on retaining events; record_events can be False.
    """
    if type(seed) is not int:
        raise ValueError("seed must be an integer for reproducible experiments")
    if type(warmup_arrivals) is not int or not 0 <= warmup_arrivals < len(arrivals):
        raise ValueError("warmup_arrivals must leave at least one measured arrival")
    if model is None:
        model = ModelSettings()
    if policy == "greedy":
        allocation_policy = GreedyPolicy(max_servers=len(model.speedups))
        policy_seed = None
    elif policy == "randomized":
        if type(policy_seed) is not int:
            raise ValueError("A reproducible comparison requires an integer policy_seed")
        allocation_policy = RandomizedPolicy(seed=policy_seed)
    else:
        raise ValueError("Unknown allocation policy")
    result = Simulator(
        servers=model.servers, policy=allocation_policy, speedups=model.speedups,
        record_events=record_events,
    ).run(arrivals, warmup_arrivals=warmup_arrivals)
    statistics = result["statistics"]
    allocations = statistics["allocations"]
    measured = len(arrivals) - warmup_arrivals
    if (result["arrivals"] != len(arrivals)
            or statistics["arrivals"] != measured
            or statistics["accepted"] + statistics["rejected"] != measured
            or sum(allocations.values()) != statistics["accepted"]
            or result["accepted"] != result["completed"]
            or result["final_idle_servers"] != model.servers):
        raise RuntimeError("The experiment finished with inconsistent counts")
    return {
        "policy": policy, "seed": seed, "policy_seed": policy_seed,
        "workload_sha256": workload_digest(arrivals),
        "servers": model.servers,
        "arrival_rate": model.arrival_rate,
        "normalized_load": model.normalized_load, "mean_job_size": model.mean_job_size,
        "speedups": list(model.speedups), "max_servers_per_job": len(model.speedups),
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


def run_trial(
    seed: int,
    warmup_arrivals: int,
    measured_arrivals: int,
    servers: int = 100,
    policy: str = "greedy",
    record_events: bool = True,
) -> dict:
    """Generate a fresh baseline workload and run either policy at a given size."""
    model = ModelSettings(servers=servers)
    if type(seed) is not int:
        raise ValueError("seed must be an integer for reproducible experiments")
    if type(warmup_arrivals) is not int or warmup_arrivals < 0:
        raise ValueError("warmup_arrivals must be a nonnegative integer")
    if type(measured_arrivals) is not int or measured_arrivals < 1:
        raise ValueError("measured_arrivals must be a positive integer")
    arrivals = WorkloadGenerator(model.arrival_rate, model.mean_job_size, seed=seed).generate(
        warmup_arrivals + measured_arrivals)
    if len(arrivals) != warmup_arrivals + measured_arrivals:
        raise RuntimeError("The workload generator returned an unexpected job count")
    return run_policy(
        arrivals, seed, policy, warmup_arrivals,
        policy_seed=ExperimentSettings().policy_seed_offset + seed,
        model=model,
        record_events=record_events,
    )
