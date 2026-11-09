"""Run one seeded simulation of the paper's randomized allocation rule."""

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


def main() -> None:
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
