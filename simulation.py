"""A greedy event loop with fixed arrival times and job sizes (M3)."""

import heapq
import math
from typing import Iterable


SPEEDUPS = (1.0, 1.8, 2.5, 3.0, 3.4)
EXAMPLE_ARRIVALS = [(0.0, 3.4), (0.2, 1.0), (0.4, 1.0), (1.0, 3.4)]


def simulate(arrivals: Iterable[tuple[float, float]], servers: int = 100) -> dict:
    """Process (arrival time, inherent job size) pairs in input order.

    Arrival times must be nonnegative and nondecreasing. A completion releases
    all of a job's servers together. At equal times, completions come first.
    After the final arrival, finish all remaining jobs.
    """
    if type(servers) is not int or servers < 1:
        raise ValueError("servers must be a positive integer")

    idle_servers = servers
    current_time = 0.0
    previous_arrival = 0.0
    arrivals_seen = accepted = rejected = completed = 0
    # Heap entries: (completion time, job id, allocated servers).
    completions = []
    events = []

    def record(event: str, job_id: int, allocated_servers: int) -> None:
        occupied_servers = sum(item[2] for item in completions)
        if not 0 <= idle_servers <= servers or idle_servers + occupied_servers != servers:
            raise RuntimeError("Server conservation failed")
        if accepted != completed + len(completions):
            raise RuntimeError("Accepted-job conservation failed")
        if arrivals_seen != accepted + rejected:
            raise RuntimeError("Arrival conservation failed")
        if events and current_time < events[-1]["time"]:
            raise RuntimeError("Events went backwards in time")
        events.append({
            "time": current_time,
            "event": event,
            "job_id": job_id,
            "allocated_servers": allocated_servers,
            "idle_servers": idle_servers,
        })

    def complete_next() -> None:
        nonlocal current_time, idle_servers, completed
        current_time, job_id, allocation = heapq.heappop(completions)
        idle_servers += allocation
        completed += 1
        record("completed", job_id, allocation)

    for job_id, (arrival_time, job_size) in enumerate(arrivals, start=1):
        if not math.isfinite(arrival_time) or arrival_time < previous_arrival:
            raise ValueError("Arrival times must be finite, nonnegative, and nondecreasing")
        if not math.isfinite(job_size) or job_size < 0:
            raise ValueError("Job sizes must be finite and nonnegative")
        previous_arrival = arrival_time

        # Finish every job due before or at this arrival.
        while completions and completions[0][0] <= arrival_time:
            complete_next()

        current_time = arrival_time
        arrivals_seen += 1
        if idle_servers == 0:
            rejected += 1
            record("rejected", job_id, 0)
            continue

        allocation = min(len(SPEEDUPS), idle_servers)
        duration = job_size / SPEEDUPS[allocation - 1]
        completion_time = current_time + duration
        if not math.isfinite(completion_time):
            raise ValueError("Completion time must be finite")
        idle_servers -= allocation
        accepted += 1
        heapq.heappush(completions, (completion_time, job_id, allocation))
        record("accepted", job_id, allocation)

    # Drain the system after arrivals stop.
    while completions:
        complete_next()

    return {
        "events": events,
        "arrivals": arrivals_seen,
        "accepted": accepted,
        "rejected": rejected,
        "completed": completed,
        "final_idle_servers": idle_servers,
    }


def main():
    result = simulate(EXAMPLE_ARRIVALS, servers=6)
    print("Fixed-input example: 6 servers, at most 5 per job")
    print(f"{'Time':>4}  {'Event':<30}  Idle servers")
    for event in result["events"]:
        description = f"Job {event['job_id']} {event['event']}"
        if event["event"] == "accepted":
            allocation = event["allocated_servers"]
            unit = "server" if allocation == 1 else "servers"
            description += f" ({allocation} {unit})"
        print(f"{event['time']:4.1f}  {description:<30}  {event['idle_servers']:>12}")
    print(f"Arrivals: {result['arrivals']}; accepted: {result['accepted']}; "
          f"rejected: {result['rejected']}; completed: {result['completed']}")
    print(f"Final idle servers: {result['final_idle_servers']}")


if __name__ == "__main__":
    main()
