"""A greedy event loop with jobs, a server pool, and performance statistics."""

import heapq
import math
from typing import Iterable


SPEEDUPS = (1.0, 1.8, 2.5, 3.0, 3.4)


class Job:
    """One job, with an allocation fixed when execution starts."""

    def __init__(self, job_id: int, arrival_time: float, size: float) -> None:
        if type(job_id) is not int or job_id < 1:
            raise ValueError("job_id must be a positive integer")
        if not math.isfinite(arrival_time) or arrival_time < 0:
            raise ValueError("Arrival times must be finite and nonnegative")
        if not math.isfinite(size) or size < 0:
            raise ValueError("Job sizes must be finite and nonnegative")
        self.job_id = job_id
        self.arrival_time = arrival_time
        self.size = size
        self.allocated_servers = 0
        self.completion_time: float | None = None

    def start(self, allocated_servers: int) -> None:
        """Set the allocation once and store the resulting completion time."""
        if self.completion_time is not None:
            raise RuntimeError("The job has already started")
        if type(allocated_servers) is not int or not 1 <= allocated_servers <= len(SPEEDUPS):
            raise ValueError("Allocation must be between 1 and the number of speedups")
        duration = self.size / SPEEDUPS[allocated_servers - 1]
        completion_time = self.arrival_time + duration
        if not math.isfinite(completion_time):
            raise ValueError("Completion time must be finite")
        self.allocated_servers = allocated_servers
        self.completion_time = completion_time


class ServerPool:
    """Manage the capacity of a pool of identical servers."""

    def __init__(self, servers: int):
        if type(servers) is not int or servers < 1:
            raise ValueError("servers must be a positive integer")
        self.total_servers = servers
        self.idle_servers = servers

    @property
    def occupied_servers(self) -> int:
        return self.total_servers - self.idle_servers

    def allocate(self, count: int) -> None:
        """Reserve exactly count idle servers."""
        if type(count) is not int or count < 1:
            raise ValueError("Allocation must be a positive integer")
        if count > self.idle_servers:
            raise ValueError("Not enough idle servers")
        self.idle_servers -= count

    def release(self, count: int) -> None:
        """Return exactly count occupied servers to the pool."""
        if type(count) is not int or count < 1:
            raise ValueError("Release count must be a positive integer")
        if count > self.occupied_servers:
            raise ValueError("Cannot release more servers than are occupied")
        self.idle_servers += count


class Statistics:
    """Measure jobs whose arrival numbers follow the warm-up cutoff."""

    def __init__(self, warmup_arrivals: int = 0) -> None:
        if type(warmup_arrivals) is not int or warmup_arrivals < 0:
            raise ValueError("warmup_arrivals must be a nonnegative integer")
        self.warmup_arrivals = warmup_arrivals
        self.arrivals = 0
        self.accepted = 0
        self.rejected = 0
        self.total_execution_time = 0.0

    def record_arrival(self, job: Job) -> None:
        """Record a job after the simulator has decided whether to start it."""
        if job.job_id <= self.warmup_arrivals:
            return
        if job.completion_time is None:
            self.rejected += 1
        else:
            self.accepted += 1
            # The full duration is already known, even if completion is later.
            self.total_execution_time += job.completion_time - job.arrival_time
        self.arrivals += 1

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


class Simulator:
    """Advance time, process jobs, and record a greedy simulation."""

    pool: ServerPool
    statistics: Statistics
    current_time: float
    arrivals_seen: int
    accepted: int
    rejected: int
    completed: int
    completions: list[tuple[float, int, Job]]
    events: list[dict]

    def __init__(self, servers: int = 100):
        self.servers = servers
        self._reset()

    def _reset(self, warmup_arrivals: int = 0) -> None:
        self.statistics = Statistics(warmup_arrivals)
        self.pool = ServerPool(self.servers)
        self.current_time = 0.0
        self.arrivals_seen = 0
        self.accepted = 0
        self.rejected = 0
        self.completed = 0
        # The unique job ID breaks time ties without comparing Job objects.
        self.completions = []
        self.events = []

    def record(self, event: str, job: Job) -> None:
        active_allocation = sum(job.allocated_servers for _, _, job in self.completions)
        if (not 0 <= self.pool.idle_servers <= self.pool.total_servers
                or self.pool.idle_servers + active_allocation != self.pool.total_servers):
            raise RuntimeError("Server conservation failed")
        if self.accepted != self.completed + len(self.completions):
            raise RuntimeError("Accepted-job conservation failed")
        if self.arrivals_seen != self.accepted + self.rejected:
            raise RuntimeError("Arrival conservation failed")
        if self.events and self.current_time < self.events[-1]["time"]:
            raise RuntimeError("Events went backwards in time")
        self.events.append({
            "time": self.current_time,
            "event": event,
            "job_id": job.job_id,
            "allocated_servers": job.allocated_servers,
            "idle_servers": self.pool.idle_servers,
        })

    def complete_next(self) -> None:
        self.current_time, _, job = heapq.heappop(self.completions)
        self.pool.release(job.allocated_servers)
        self.completed += 1
        self.record("completed", job)

    def handle_arrival(self, job: Job) -> None:
        if job.arrival_time < self.current_time:
            raise ValueError("Arrival times must be nondecreasing")
        # Release every job due before or at this arrival.
        while self.completions and self.completions[0][0] <= job.arrival_time:
            self.complete_next()

        self.current_time = job.arrival_time
        self.arrivals_seen += 1
        if self.pool.idle_servers == 0:
            self.rejected += 1
            self.statistics.record_arrival(job)
            self.record("rejected", job)
            return

        allocation = min(len(SPEEDUPS), self.pool.idle_servers)
        job.start(allocation)
        assert job.completion_time is not None
        self.pool.allocate(allocation)
        self.accepted += 1
        heapq.heappush(self.completions, (job.completion_time, job.job_id, job))
        self.statistics.record_arrival(job)
        self.record("accepted", job)

    def run(
        self,
        arrivals: Iterable[tuple[float, float]],
        warmup_arrivals: int = 0,
    ) -> dict:
        """Run ordered (arrival time, size) pairs, starting from an empty system.

        Completions at an arrival's timestamp are processed first. After the
        final arrival, finish all remaining jobs. Each call starts a fresh run.
        Process the first warmup_arrivals normally but exclude them from
        statistics. All event-log entries and top-level counts cover the run.
        """
        self._reset(warmup_arrivals)
        for job_id, (arrival_time, job_size) in enumerate(arrivals, start=1):
            job = Job(job_id=job_id, arrival_time=arrival_time, size=job_size)
            self.handle_arrival(job)

        while self.completions:
            self.complete_next()

        return {
            "events": self.events,
            "arrivals": self.arrivals_seen,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "completed": self.completed,
            "final_idle_servers": self.pool.idle_servers,
            "statistics": {
                "warmup_arrivals": self.statistics.warmup_arrivals,
                "arrivals": self.statistics.arrivals,
                "accepted": self.statistics.accepted,
                "rejected": self.statistics.rejected,
                "total_execution_time": self.statistics.total_execution_time,
                "blocking_probability": self.statistics.blocking_probability,
                "mean_execution_time": self.statistics.mean_execution_time,
            },
        }
