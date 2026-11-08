"""Model and experiment inputs for job-scheduling simulations."""

import math


_SPEEDUP_TOLERANCE = 1e-12


def _require_integer(value: int, name: str, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        requirement = "positive" if minimum == 1 else "nonnegative"
        raise ValueError(f"{name} must be a {requirement} integer")


def _require_finite_number(value: float, name: str) -> None:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{name} must be a finite number")


def _as_tuple(values: tuple | list, name: str) -> tuple:
    if not isinstance(values, (tuple, list)) or not values:
        raise ValueError(f"{name} must be a nonempty list or tuple")
    return tuple(values)


class ModelSettings:
    """Validate and store the model inputs for one simulation configuration.

    Load must be strictly between 0 and 1. Speedups start at 1, increase
    strictly, and are concave, including the gain from zero to one server.
    Invalid inputs raise ValueError.
    """

    def __init__(
        self,
        servers: int = 100,
        normalized_load: float = 0.8,
        mean_job_size: float = 1.0,
        speedups: tuple[float, ...] | list[float] = (1.0, 1.8, 2.5, 3.0, 3.4),
    ) -> None:
        _require_integer(servers, "servers", minimum=1)
        _require_finite_number(normalized_load, "normalized_load")
        if not 0 < normalized_load < 1:
            raise ValueError("normalized_load must be strictly between 0 and 1")
        _require_finite_number(mean_job_size, "mean_job_size")
        if mean_job_size <= 0:
            raise ValueError("mean_job_size must be positive")

        speedups = _as_tuple(speedups, "speedups")
        for value in speedups:
            _require_finite_number(value, "speedups")
        if speedups[0] != 1:
            raise ValueError("speedups must start at 1 for a single server")
        previous_gain = 1.0  # The first gain is s1 - s0 = 1 - 0.
        for previous, current in zip(speedups, speedups[1:]):
            gain = current - previous
            if gain <= 0:
                raise ValueError("speedups must be strictly increasing")
            # Equal gains can differ slightly after floating-point subtraction.
            if gain > previous_gain and not math.isclose(
                gain, previous_gain,
                rel_tol=_SPEEDUP_TOLERANCE, abs_tol=_SPEEDUP_TOLERANCE,
            ):
                raise ValueError("speedups must be concave: gains cannot increase")
            previous_gain = gain

        self.servers = servers
        self.normalized_load = normalized_load
        self.mean_job_size = mean_job_size
        self.speedups = speedups


class ExperimentSettings:
    """Validate and store inputs for repeated experiments and comparisons.

    At least two unique nonnegative workload seeds support across-run statistics.
    Policy seeds use a positive offset and must not overlap the workload seeds.
    Confidence level is a fraction, such as 0.95 for 95%.
    Invalid inputs raise ValueError.
    """

    def __init__(
        self,
        seeds: tuple[int, ...] | list[int] = tuple(range(10)),
        policy_seed_offset: int = 10_000,
        warmup_arrivals: int = 10_000,
        measured_arrivals: int = 100_000,
        server_counts: tuple[int, ...] | list[int] = (25, 50, 100, 200, 500, 1_000),
        sensitivity_thresholds: dict[str, float] | None = None,
        confidence_level: float = 0.95,
    ) -> None:
        seeds = _as_tuple(seeds, "seeds")
        for seed in seeds:
            _require_integer(seed, "seeds", minimum=0)
        if len(seeds) < 2 or len(set(seeds)) != len(seeds):
            raise ValueError("seeds must contain at least two unique workload seeds")
        _require_integer(policy_seed_offset, "policy_seed_offset", minimum=1)
        policy_seeds = {policy_seed_offset + seed for seed in seeds}
        if policy_seeds.intersection(seeds):
            raise ValueError("workload and policy seeds must not overlap")
        _require_integer(warmup_arrivals, "warmup_arrivals", minimum=0)
        _require_integer(measured_arrivals, "measured_arrivals", minimum=1)

        server_counts = _as_tuple(server_counts, "server_counts")
        for servers in server_counts:
            _require_integer(servers, "server_counts", minimum=1)
        if len(set(server_counts)) != len(server_counts):
            raise ValueError("server_counts must contain unique values")

        if sensitivity_thresholds is None:
            sensitivity_thresholds = {
                "blocking_probability": 0.002, "mean_execution_time": 0.002,
            }
        metrics = {"blocking_probability", "mean_execution_time"}
        if not isinstance(sensitivity_thresholds, dict) or set(sensitivity_thresholds) != metrics:
            raise ValueError(
                "sensitivity_thresholds must define blocking_probability and mean_execution_time"
            )
        for metric, threshold in sensitivity_thresholds.items():
            _require_finite_number(threshold, f"sensitivity_thresholds[{metric!r}]")
            if threshold < 0:
                raise ValueError("sensitivity_thresholds must be nonnegative")
        _require_finite_number(confidence_level, "confidence_level")
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be strictly between 0 and 1")

        self.seeds = seeds
        self.policy_seed_offset = policy_seed_offset
        self.warmup_arrivals = warmup_arrivals
        self.measured_arrivals = measured_arrivals
        self.server_counts = server_counts
        self.sensitivity_thresholds = dict(sensitivity_thresholds)
        self.confidence_level = confidence_level
