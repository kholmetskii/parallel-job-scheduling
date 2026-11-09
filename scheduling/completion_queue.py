"""Scheduled job completions ordered by time and job ID."""

import heapq

from scheduling.job import Job


class CompletionQueue:
    """Keep each running job's completion time and allocated servers."""

    def __init__(self) -> None:
        self._heap: list[tuple[float, int, int, Job]] = []

    def __bool__(self) -> bool:
        return bool(self._heap)

    def schedule(self, completion_time: float, job: Job, allocated_servers: int) -> None:
        """Add a completion; unique job IDs break simultaneous-completion ties."""
        heapq.heappush(self._heap, (completion_time, job.id, allocated_servers, job))

    def peek_time(self) -> float:
        """Return the earliest completion time; the queue must be nonempty."""
        return self._heap[0][0]

    def pop_next(self) -> tuple[float, int, Job]:
        """Remove the earliest completion and return its time, allocation, and job."""
        completion_time, _, allocation, job = heapq.heappop(self._heap)
        return completion_time, allocation, job
