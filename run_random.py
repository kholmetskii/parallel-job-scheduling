"""Run a small, reproducible random-workload example for M4."""

from simulation import Simulator
from workload import WorkloadGenerator


def main() -> None:
    servers = 100
    num_jobs = 1000
    seed = 42
    workload = WorkloadGenerator(
        arrival_rate=0.8 * servers,
        mean_job_size=1.0,
        seed=seed,
    )
    arrivals = workload.generate(num_jobs=num_jobs)
    result = Simulator(servers=servers).run(arrivals)

    print(f"Random workload: servers={servers}, jobs={num_jobs}, seed={seed}")
    print(f"Arrival rate: {workload.arrival_rate}; "
          f"mean job size: {workload.mean_job_size}")
    print(f"Arrivals: {result['arrivals']}; accepted: {result['accepted']}; "
          f"rejected: {result['rejected']}; completed: {result['completed']}")
    print(f"Final idle servers: {result['final_idle_servers']}")


if __name__ == "__main__":
    main()
