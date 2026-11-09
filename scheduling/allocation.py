"""Optimal single-class allocation targets and probabilities from the paper."""

import math

_SPEEDUP_TOLERANCE = 1e-12


def validate_speedups(speedups: tuple[float, ...] | list[float]) -> tuple[float, ...]:
    """Return an immutable, increasing concave speedup curve starting at one."""
    if not isinstance(speedups, (tuple, list)) or not speedups:
        raise ValueError("speedups must be a nonempty list or tuple")
    speedups = tuple(speedups)
    for value in speedups:
        try:
            finite = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError("speedups must be finite numbers")
    if speedups[0] != 1:
        raise ValueError("speedups must start at 1 for a single server")
    previous_gain = 1.0  # The first gain is s1 - s0 = 1 - 0.
    for previous, current in zip(speedups, speedups[1:]):
        gain = current - previous
        if gain <= 0:
            raise ValueError("speedups must be strictly increasing")
        if gain > previous_gain and not math.isclose(
            gain, previous_gain, rel_tol=_SPEEDUP_TOLERANCE, abs_tol=_SPEEDUP_TOLERANCE,
        ):
            raise ValueError("speedups must be concave: gains cannot increase")
        previous_gain = gain
    return speedups


def optimal_allocation_targets(
    normalized_load: float,
    speedups: tuple[float, ...] | list[float],
) -> tuple[int, ...]:
    """Return one optimal target or two neighbouring targets in increasing order.

    Compare load with efficiencies s_i / i. At or below s_d / d, use d;
    at an efficiency boundary, use the largest matching target; otherwise
    use the neighbours whose efficiencies bracket the load. Load must be strictly
    between zero and one; speedups must be increasing and concave, starting at one.

    A four-ulp tolerance absorbs division round-off at boundaries below 1.
    Probabilities and allocation sampling are calculated separately.
    """
    if type(normalized_load) not in (int, float) or not 0 < normalized_load < 1:
        raise ValueError("normalized_load must be strictly between 0 and 1")
    speedups = validate_speedups(speedups)
    maximum = len(speedups)
    for target in range(maximum, 0, -1):
        efficiency = speedups[target - 1] / target
        # Unit efficiency would require load 1 for equality, which is excluded.
        at_boundary = efficiency < 1 and math.isclose(
            normalized_load, efficiency,
            rel_tol=0.0, abs_tol=4 * math.ulp(efficiency),
        )
        if at_boundary:
            return (target,)
        if normalized_load < efficiency:
            return (target,) if target == maximum else (target, target + 1)

    raise AssertionError("Validated load must be below the single-server efficiency")


def optimal_allocation_probabilities(
    normalized_load: float,
    speedups: tuple[float, ...] | list[float],
) -> tuple[float, ...]:
    """Return probabilities in the order given by optimal_allocation_targets().

    A single target has probability 1. For a neighbouring pair, calculate
    y_i and y_(i+1) using Theorem 1, equations (8)-(9), then p_i = s_i*y_i/load
    as in Section IV. Normalize the result to absorb floating-point round-off.
    Input validation and boundary handling are shared with target selection.
    """
    targets = optimal_allocation_targets(normalized_load, speedups)
    if len(targets) == 1:
        return (1.0,)

    lower, upper = targets
    lower_efficiency = speedups[lower - 1] / lower
    upper_efficiency = speedups[upper - 1] / upper
    efficiency_gap = lower_efficiency - upper_efficiency
    lower_y = (normalized_load - upper_efficiency) / (lower * efficiency_gap)
    upper_y = (lower_efficiency - normalized_load) / (upper * efficiency_gap)
    probabilities = (
        speedups[lower - 1] * lower_y / normalized_load,
        speedups[upper - 1] * upper_y / normalized_load,
    )
    total = math.fsum(probabilities)
    return tuple(probability / total for probability in probabilities)
