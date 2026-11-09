"""Execution of moldable jobs on a pool of identical servers."""

import math

from scheduling.completion_queue import CompletionQueue
from scheduling.job import Job


class ServerPool:
    """Own server capacity and the lifecycle of running jobs."""

    def __init__(
        self,
        servers: int,
        speedups: tuple[float, ...] | list[float],
    ) -> None:
        self.total_servers = servers
        self.speedups = tuple(speedups)
        self.max_servers_per_job = len(self.speedups)
        self._idle_servers = self.total_servers
        self._completion_queue = CompletionQueue()

    @property
    def idle_servers(self) -> int:
        return self._idle_servers

    @property
    def occupied_servers(self) -> int:
        return self.total_servers - self.idle_servers

    def start_job(self, job: Job, allocated_servers: int) -> float | None:
        """Reserve servers and schedule completion, or return None for a blocked job.

        A zero allocation is valid only when all servers are occupied. Job IDs
        are supplied uniquely by the workload generator.
        """
        if (type(allocated_servers) is not int
                or not 0 <= allocated_servers <= min(self.max_servers_per_job, self.idle_servers)
                or (allocated_servers == 0 and self.idle_servers > 0)):
            raise ValueError("Allocation must fit available capacity and the model's limits")
        if allocated_servers == 0:
            return None

        duration = job.size / self.speedups[allocated_servers - 1]
        completion_time = job.arrival_time + duration
        if not math.isfinite(completion_time):
            raise ValueError("Completion time must be finite")
        self._completion_queue.schedule(completion_time, job, allocated_servers)
        self._idle_servers -= allocated_servers
        return completion_time

    def next_completion_time(self) -> float | None:
        """Return the next scheduled completion time, or None when no job is running."""
        return self._completion_queue.peek_time() if self._completion_queue else None

    def complete_next(self) -> tuple[float, int, Job]:
        """Complete the earliest job, release its servers, and return its details."""
        completion_time, allocation, job = self._completion_queue.pop_next()
        self._idle_servers += allocation
        return completion_time, allocation, job
