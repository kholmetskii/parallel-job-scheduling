"""Shared immutable job inputs for simulator and statistics checks."""

from scheduling.job import Job


SPEEDUPS = (1, 1.8, 2.5, 3, 3.4)


def make_jobs(arrivals: list[tuple[float, float]]) -> list[Job]:
    """Build jobs from concise (arrival time, size) test examples."""
    return [Job(id=index, size=size, arrival_time=time)
            for index, (time, size) in enumerate(arrivals, start=1)]


EXAMPLE_ARRIVALS = make_jobs([(0.0, 3.4), (0.2, 1.0), (0.4, 1.0), (1.0, 3.4)])
