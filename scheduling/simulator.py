"""An event loop coordinating jobs, allocation policies, and statistics."""

from typing import Iterable, Literal

from scheduling.allocation import validate_speedups
from scheduling.job import Job
from scheduling.logger import Logger
from scheduling.policies import GreedyPolicy, RandomizedPolicy
from scheduling.server_pool import ServerPool
from scheduling.statistics import Statistics


class Simulator:
    """Advance time, process jobs, and record a simulation under one policy."""

    pool: ServerPool
    statistics: Statistics
    current_time: float
    logger: Logger

    def __init__(
        self,
        servers: int,
        policy: GreedyPolicy | RandomizedPolicy | None = None,
        *,
        speedups: tuple[float, ...] | list[float],
        record_events: bool = True,
    ):
        self._servers = servers
        self._speedups = validate_speedups(speedups)
        self._record_events = record_events
        self.policy = (GreedyPolicy(max_servers=len(self._speedups))
                       if policy is None else policy)
        self._reset()

    def _reset(self, warmup_arrivals: int = 0) -> None:
        self.pool = ServerPool(self._servers, self._speedups)
        self.statistics = Statistics(warmup_arrivals, self.pool.max_servers_per_job)
        self.current_time = 0.0
        self.logger = Logger(enabled=self._record_events)
        self.policy.reset()

    def handle_completion(self) -> None:
        """Advance the clock to a pool completion and notify the observers."""
        self.current_time, allocation, job = self.pool.complete_next()
        self.statistics.record_completion()
        self.logger.record(
            self.current_time, "completed", job.id, allocation, self.pool.idle_servers,
        )

    def handle_arrival(self, job: Job) -> None:
        if job.arrival_time < self.current_time:
            raise ValueError("Arrival times must be nondecreasing")
        # Release every job due before or at this arrival.
        next_completion = self.pool.next_completion_time()
        while next_completion is not None and next_completion <= job.arrival_time:
            self.handle_completion()
            next_completion = self.pool.next_completion_time()

        self.current_time = job.arrival_time
        allocation = self.policy.choose_allocation(self.pool.idle_servers)
        completion_time = self.pool.start_job(job, allocation)
        execution_time = None if completion_time is None else completion_time - job.arrival_time
        kind: Literal["accepted", "rejected"] = "rejected" if completion_time is None else "accepted"
        self.statistics.record_arrival(allocation, execution_time)
        self.logger.record(self.current_time, kind, job.id, allocation, self.pool.idle_servers)

    def run(
        self,
        arrivals: Iterable[Job],
        warmup_arrivals: int = 0,
    ) -> dict:
        """Run immutable jobs in arrival order, starting from an empty system.

        Completions at an arrival's timestamp are processed first. After the
        final arrival, finish all remaining jobs. Each call starts a fresh run.
        Process the first warmup_arrivals normally but exclude them from
        statistics. All event-log entries and top-level counts cover the run.
        Reset the policy's random stream along with the simulator state.
        Job IDs must be unique within the run; warm-up follows arrival order.
        The returned event log contains immutable Event objects.
        With record_events=False, the log is empty and measurements are unchanged.
        """
        self._reset(warmup_arrivals)
        seen_ids = set()
        for job in arrivals:
            if not isinstance(job, Job):
                raise ValueError("arrivals must contain Job objects")
            if job.id in seen_ids:
                raise ValueError("Job IDs must be unique within a run")
            seen_ids.add(job.id)
            self.handle_arrival(job)

        while self.pool.next_completion_time() is not None:
            self.handle_completion()

        return {
            "events": self.logger.events,
            "arrivals": self.statistics.total_arrivals,
            "accepted": self.statistics.total_accepted,
            "rejected": self.statistics.total_rejected,
            "completed": self.statistics.total_completed,
            "final_idle_servers": self.pool.idle_servers,
            "statistics": self.statistics.summary(),
        }
