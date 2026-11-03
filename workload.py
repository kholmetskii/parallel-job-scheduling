"""Generate Poisson arrivals with independent exponential job sizes."""

import math
import random


class WorkloadGenerator:
    """Store workload settings and a local random number generator."""

    def __init__(
        self,
        arrival_rate: float,
        mean_job_size: float = 1.0,
        seed: int | None = None,
    ) -> None:
        if not math.isfinite(arrival_rate) or arrival_rate <= 0:
            raise ValueError("arrival_rate must be finite and positive")
        if not math.isfinite(mean_job_size) or mean_job_size <= 0:
            raise ValueError("mean_job_size must be finite and positive")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.arrival_rate = arrival_rate
        self.mean_job_size = mean_job_size
        self.seed = seed
        self.rng = random.Random(seed)

    def generate(self, num_jobs: int) -> list[tuple[float, float]]:
        """Return ordered (arrival time, size) pairs for a fixed job count.

        Each call starts the arrival clock at zero and continues this object's
        random stream. A fresh generator with the same seed reproduces it.
        """
        if type(num_jobs) is not int or num_jobs < 0:
            raise ValueError("num_jobs must be a nonnegative integer")

        arrivals = []
        arrival_time = 0.0
        for _ in range(num_jobs):
            gap = self.rng.expovariate(self.arrival_rate)
            arrival_time += gap
            job_size = self.rng.expovariate(1.0 / self.mean_job_size)
            arrivals.append((arrival_time, job_size))
        return arrivals
