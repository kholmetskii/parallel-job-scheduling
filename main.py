"""Run one seeded simulation of the paper's randomized allocation rule."""

import math

from scheduling.allocation import optimal_allocation_probabilities, optimal_allocation_targets
from scheduling.policies import RandomizedPolicy
from scheduling.simulator import Simulator
from scheduling.workload import WorkloadGenerator


SERVERS = 100
NORMALIZED_LOAD = 0.8
MEAN_JOB_SIZE = 1.0
SPEEDUPS = (1.0, 1.8, 2.5, 3.0, 3.4)
WORKLOAD_SEED = 0
POLICY_SEED = 10_000
WARMUP_ARRIVALS = 10_000
MEASURED_ARRIVALS = 100_000


def validate_configuration() -> None:
    """Check the model assumptions and run lengths once, before generating jobs."""
    for name, value, minimum in (
        ("SERVERS", SERVERS, 1),
        ("WARMUP_ARRIVALS", WARMUP_ARRIVALS, 0),
        ("MEASURED_ARRIVALS", MEASURED_ARRIVALS, 1),
    ):
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer at least {minimum}")
    if not 0 < NORMALIZED_LOAD < 1:
        raise ValueError("NORMALIZED_LOAD must be strictly between 0 and 1")
    if not math.isfinite(MEAN_JOB_SIZE) or MEAN_JOB_SIZE <= 0:
        raise ValueError("MEAN_JOB_SIZE must be finite and positive")
    arrival_rate = NORMALIZED_LOAD * SERVERS / MEAN_JOB_SIZE
    if not math.isfinite(arrival_rate) or arrival_rate <= 0:
        raise ValueError("The derived arrival rate must be finite and positive")
    if not SPEEDUPS or SPEEDUPS[0] != 1 or not all(math.isfinite(s) for s in SPEEDUPS):
        raise ValueError("SPEEDUPS must be finite, nonempty and start at 1")
    gains = [current - previous for previous, current in zip((0, *SPEEDUPS), SPEEDUPS)]
    if any(gain <= 0 for gain in gains) or any(
        current > previous and not math.isclose(current, previous, rel_tol=1e-12, abs_tol=1e-12)
        for previous, current in zip(gains, gains[1:])
    ):
        raise ValueError("SPEEDUPS must be increasing and concave")


def main() -> None:
    validate_configuration()
    arrival_rate = NORMALIZED_LOAD * SERVERS / MEAN_JOB_SIZE
    arrivals = WorkloadGenerator(
        arrival_rate, MEAN_JOB_SIZE, seed=WORKLOAD_SEED,
    ).generate(WARMUP_ARRIVALS + MEASURED_ARRIVALS)
    targets = optimal_allocation_targets(NORMALIZED_LOAD, SPEEDUPS)
    probabilities = optimal_allocation_probabilities(NORMALIZED_LOAD, SPEEDUPS)
    policy = RandomizedPolicy(targets, probabilities, seed=POLICY_SEED)
    simulator = Simulator(
        servers=SERVERS, policy=policy, speedups=SPEEDUPS, record_events=False,
    )
    statistics = simulator.run(arrivals, warmup_arrivals=WARMUP_ARRIVALS)["statistics"]

    print(f"Servers: {SERVERS}; workload seed: {WORKLOAD_SEED}; policy seed: {POLICY_SEED}")
    print(f"Warm-up: {WARMUP_ARRIVALS}; measured arrivals: {MEASURED_ARRIVALS}")
    print(f"Blocking probability: {statistics['blocking_probability']:.6f}")
    print(f"Mean execution time: {statistics['mean_execution_time']:.6f}")


if __name__ == "__main__":
    main()
