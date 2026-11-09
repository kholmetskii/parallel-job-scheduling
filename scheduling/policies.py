"""Greedy and randomized server allocation rules."""

import math
import random


class GreedyPolicy:
    """Choose as many idle servers as possible, up to the job's maximum."""

    def __init__(self, max_servers: int = 5) -> None:
        if type(max_servers) is not int or max_servers < 1:
            raise ValueError("max_servers must be a positive integer")
        self.max_servers = max_servers

    def reset(self) -> None:
        """Start a new run; this policy has no random state."""

    def choose_allocation(self, idle_servers: int) -> int:
        if type(idle_servers) is not int or idle_servers < 0:
            raise ValueError("idle_servers must be a nonnegative integer")
        return min(self.max_servers, idle_servers)


class RandomizedPolicy:
    """Sample a supplied target distribution and cap it by idle capacity.

    The caller supplies the target distribution. A target
    is sampled for every arrival, including blocked jobs and single-target cases.
    """

    def __init__(
        self,
        targets: tuple[int, ...] | list[int],
        probabilities: tuple[float, ...] | list[float],
        seed: int | None = None,
    ) -> None:
        if (not isinstance(targets, (tuple, list)) or not targets
                or any(type(target) is not int or target < 1 for target in targets)
                or len(set(targets)) != len(targets)):
            raise ValueError("targets must be a nonempty sequence of unique positive integers")
        if (not isinstance(probabilities, (tuple, list))
                or len(probabilities) != len(targets)
                or any(type(p) not in (int, float) or not 0 <= p <= 1
                       or not math.isfinite(p) for p in probabilities)):
            raise ValueError("probabilities must match targets and be finite values between 0 and 1")
        total = math.fsum(probabilities)
        if not math.isclose(total, 1.0, rel_tol=1e-12, abs_tol=0.0):
            raise ValueError("probabilities must sum to 1")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.targets = tuple(targets)
        self.probabilities = tuple(p / total for p in probabilities)
        self.seed = seed
        self.rng = random.Random(seed)

    def reset(self) -> None:
        """Restart the policy's random stream for a fresh simulator run."""
        self.rng.seed(self.seed)

    def choose_allocation(self, idle_servers: int) -> int:
        if type(idle_servers) is not int or idle_servers < 0:
            raise ValueError("idle_servers must be a nonnegative integer")
        target = self.rng.choices(self.targets, weights=self.probabilities, k=1)[0]
        return min(target, idle_servers)
