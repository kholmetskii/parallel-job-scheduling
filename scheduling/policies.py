"""Greedy and randomized server allocation rules."""

import math
import random
from typing import Protocol

from .allocation import optimal_allocation_probabilities, optimal_allocation_targets


class AllocationPolicy(Protocol):
    """Operations the simulator needs from an allocation policy."""

    def reset(self) -> None:
        """Prepare the policy for a fresh simulation run."""
        ...

    def choose_allocation(self, idle_servers: int) -> int:
        """Return zero if no servers are idle, otherwise a positive allocation.

        The allocation must fit the available capacity and the job's limit.
        """
        ...


class GreedyPolicy:
    """Choose as many idle servers as possible, up to the job's maximum."""

    def __init__(self, max_servers: int = 5) -> None:
        self.max_servers = max_servers

    def reset(self) -> None:
        """Start a new run; this policy has no random state."""

    def choose_allocation(self, idle_servers: int) -> int:
        return min(self.max_servers, idle_servers)


class RandomizedPolicy:
    """Sample a supplied target distribution and cap it by idle capacity.

    Supply a valid distribution directly or use optimal() with the model settings.
    A target is sampled for every arrival, including blocked jobs and single-target cases.
    """

    def __init__(
        self,
        targets: tuple[int, ...] | list[int],
        probabilities: tuple[float, ...] | list[float],
        seed: int | None = None,
    ) -> None:
        total = math.fsum(probabilities)
        self.targets = tuple(targets)
        self.probabilities = tuple(p / total for p in probabilities)
        self.seed = seed
        self.rng = random.Random(seed)

    @classmethod
    def optimal(
        cls,
        normalized_load: float,
        speedups: tuple[float, ...] | list[float],
        seed: int | None = None,
    ) -> "RandomizedPolicy":
        """Construct the paper's randomized policy from validated model settings."""
        targets = optimal_allocation_targets(normalized_load, speedups)
        probabilities = optimal_allocation_probabilities(normalized_load, speedups)
        return cls(targets, probabilities, seed=seed)

    def reset(self) -> None:
        """Restart the policy's random stream for a fresh simulator run."""
        self.rng.seed(self.seed)

    def choose_allocation(self, idle_servers: int) -> int:
        target = self.rng.choices(self.targets, weights=self.probabilities, k=1)[0]
        return min(target, idle_servers)
