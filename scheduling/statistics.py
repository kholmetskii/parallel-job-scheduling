"""Whole-run counts and measurements after the warm-up cutoff."""


class Statistics:
    """Own all counts, allocation frequencies, and execution-time measurements."""

    def __init__(self, warmup_arrivals: int = 0, max_servers_per_job: int = 5) -> None:
        self.warmup_arrivals = warmup_arrivals
        self.total_arrivals = 0
        self.total_accepted = 0
        self.total_rejected = 0
        self.total_completed = 0
        self.arrivals = 0
        self.accepted = 0
        self.rejected = 0
        self.total_execution_time = 0.0
        self.allocations = {str(count): 0 for count in range(1, max_servers_per_job + 1)}

    def record_arrival(self, allocated_servers: int, execution_time: float | None) -> None:
        """Record an arrival's full execution time, or None for a rejection."""
        self.total_arrivals += 1
        if execution_time is None:
            self.total_rejected += 1
        else:
            self.total_accepted += 1
        if self.total_arrivals <= self.warmup_arrivals:
            return
        if execution_time is None:
            self.rejected += 1
        else:
            self.accepted += 1
            # The full duration is already known, even if completion is later.
            self.total_execution_time += execution_time
            self.allocations[str(allocated_servers)] += 1
        self.arrivals += 1

    def record_completion(self) -> None:
        """Count a completed job, including jobs that arrived during warm-up."""
        self.total_completed += 1

    @property
    def blocking_probability(self) -> float | None:
        if self.arrivals == 0:
            return None
        return self.rejected / self.arrivals

    @property
    def mean_execution_time(self) -> float | None:
        if self.accepted == 0:
            return None
        return self.total_execution_time / self.accepted

    def summary(self) -> dict:
        """Return a snapshot of the measured counts and performance metrics."""
        return {
            "warmup_arrivals": self.warmup_arrivals,
            "arrivals": self.arrivals,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "total_execution_time": self.total_execution_time,
            "blocking_probability": self.blocking_probability,
            "mean_execution_time": self.mean_execution_time,
            "allocations": self.allocations.copy(),
        }
