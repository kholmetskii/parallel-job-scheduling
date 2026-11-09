"""Recorded events from one simulation run."""

from typing import Literal

from scheduling.event import Event


class Logger:
    """Create and store immutable event snapshots."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.events: list[Event] = []

    def record(
        self,
        time: float,
        kind: Literal["accepted", "rejected", "completed"],
        job_id: int,
        allocated_servers: int,
        idle_servers: int,
    ) -> None:
        """Append a snapshot of what happened and the resulting server capacity."""
        if not self.enabled:
            return
        self.events.append(Event(
            time=time,
            kind=kind,
            job_id=job_id,
            allocated_servers=allocated_servers,
            idle_servers=idle_servers,
        ))
