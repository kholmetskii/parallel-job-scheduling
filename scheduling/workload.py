"""Generate Poisson arrivals with independent exponential job sizes."""

import random

from scheduling.job import Job


class WorkloadGenerator:
    """Store workload settings and a local random number generator."""

    def __init__(
        self,
        arrival_rate: float,
        mean_job_size: float = 1.0,
        seed: int | None = None,
    ) -> None:
        self.arrival_rate = arrival_rate
        self.mean_job_size = mean_job_size
        self.seed = seed
        self.rng = random.Random(seed)

    def generate(self, num_jobs: int) -> list[Job]:
        """Return immutable jobs in arrival order for a fixed job count.

        Each call restarts IDs at one and the arrival clock at zero, continuing
        this object's random stream. A fresh generator with the same seed
        reproduces the workload.
        """
        arrivals = []
        arrival_time = 0.0
        for job_id in range(1, num_jobs + 1):
            gap = self.rng.expovariate(self.arrival_rate)
            arrival_time += gap
            job_size = self.rng.expovariate(1.0 / self.mean_job_size)
            arrivals.append(Job(id=job_id, size=job_size, arrival_time=arrival_time))
        return arrivals
