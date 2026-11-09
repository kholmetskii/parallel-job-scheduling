"""Immutable input data for one arriving job."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    """A job's identity, size, and arrival time, shared safely between runs."""

    id: int
    size: float
    arrival_time: float
