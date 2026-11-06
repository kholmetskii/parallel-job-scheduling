"""Server allocation rules for the greedy and paper-policy comparison."""

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
    """Paper's greedy(p*) for normalized rate 0.8 and our fixed speedups.

    Target 3 servers with probability 0.625 and 4 otherwise, then cap by
    idle capacity. These probabilities must be recalculated for other model
    parameters. A target is sampled for every arrival, including blocked jobs.
    """

    def __init__(self, seed: int | None = None) -> None:
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed
        self.probability_three = 0.625
        self.rng = random.Random(seed)

    def reset(self) -> None:
        """Restart the policy's random stream for a fresh simulator run."""
        self.rng.seed(self.seed)

    def choose_allocation(self, idle_servers: int) -> int:
        if type(idle_servers) is not int or idle_servers < 0:
            raise ValueError("idle_servers must be a nonnegative integer")
        target = 3 if self.rng.random() < self.probability_three else 4
        return min(target, idle_servers)
