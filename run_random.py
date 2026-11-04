"""Run a reproducible random workload with warm-up and performance metrics."""

from reporting import print_summary
from simulation import Simulator
from workload import WorkloadGenerator


def main() -> None:
    servers = 100
    num_jobs = 11_000
    warmup_arrivals = 1_000
    seed = 42
    workload = WorkloadGenerator(
        arrival_rate=0.8 * servers,
        mean_job_size=1.0,
        seed=seed,
    )
    arrivals = workload.generate(num_jobs=num_jobs)
    result = Simulator(servers=servers).run(arrivals, warmup_arrivals=warmup_arrivals)

    print(f"Random workload: servers={servers}, jobs={num_jobs}, seed={seed}")
    print(f"Arrival rate: {workload.arrival_rate}; "
          f"mean job size: {workload.mean_job_size}")
    print_summary(result)


if __name__ == "__main__":
    main()
