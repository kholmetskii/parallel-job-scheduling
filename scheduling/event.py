"""Immutable records of accepted, rejected, and completed jobs."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Event:
    """A snapshot of one job event and the remaining server capacity."""

    time: float
    kind: Literal["accepted", "rejected", "completed"]
    job_id: int
    allocated_servers: int
    idle_servers: int
