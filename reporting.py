"""Shared console summaries for fixed and random simulation runners."""


def print_summary(result: dict) -> None:
    """Print whole-run counts and measurements using a common format."""
    statistics = result["statistics"]
    print(f"Arrivals: {result['arrivals']}; accepted: {result['accepted']}; "
          f"rejected: {result['rejected']}; completed: {result['completed']}")
    print(f"Final idle servers: {result['final_idle_servers']}")
    print(f"Warm-up cutoff: first {statistics['warmup_arrivals']} arrivals")
    print(f"Measured arrivals: {statistics['arrivals']}; "
          f"accepted: {statistics['accepted']}; rejected: {statistics['rejected']}")
    blocking = statistics["blocking_probability"]
    mean_time = statistics["mean_execution_time"]
    print("Blocking probability:", "unavailable" if blocking is None else f"{blocking:.6f}")
    print("Mean execution time:", "unavailable" if mean_time is None else f"{mean_time:.6f}")
