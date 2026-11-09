"""Immutable input data for one arriving job."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    """A job's identity, size, and arrival time, shared safely between runs."""

    id: int
    size: float
    arrival_time: float

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id < 1:
            raise ValueError("id must be a positive integer")
        for value, name in ((self.size, "Job sizes"), (self.arrival_time, "Arrival times")):
            try:
                valid = (type(value) in (int, float)
                         and math.isfinite(value) and value >= 0)
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError(f"{name} must be finite and nonnegative")
