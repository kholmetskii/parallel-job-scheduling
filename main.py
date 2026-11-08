"""Compare both allocation policies on one reproducible workload."""

from scheduling.config import ExperimentSettings, ModelSettings
from scheduling.experiments import run_policy
from scheduling.workload import WorkloadGenerator


def main() -> None:
    model = ModelSettings()
    experiment = ExperimentSettings()
    seed = experiment.seeds[0]
    arrival_rate = model.normalized_load * model.servers / model.mean_job_size
    arrivals = WorkloadGenerator(arrival_rate, model.mean_job_size, seed=seed).generate(
        experiment.warmup_arrivals + experiment.measured_arrivals)

    print(f"Servers: {model.servers}; workload seed: {seed}")
    print(f"Warm-up: {experiment.warmup_arrivals}; measured arrivals: {experiment.measured_arrivals}")
    print(f"{'Policy':<12} {'Blocking probability':>22} {'Mean execution time':>22}")
    for policy in ("greedy", "randomized"):
        result = run_policy(
            arrivals, seed, policy, experiment.warmup_arrivals,
            policy_seed=experiment.policy_seed_offset + seed,
            model=model,
        )
        print(f"{policy:<12} {result['blocking_probability']:>22.6f} "
              f"{result['mean_execution_time']:>22.6f}")


if __name__ == "__main__":
    main()
