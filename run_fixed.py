"""Run the hand-worked six-server example with fixed arrivals and sizes."""

from reporting import print_summary
from simulation import Simulator


EXAMPLE_ARRIVALS = [(0.0, 3.4), (0.2, 1.0), (0.4, 1.0), (1.0, 3.4)]


def main() -> None:
    servers = 6
    result = Simulator(servers=servers).run(EXAMPLE_ARRIVALS)
    print(f"Fixed workload: servers={servers}, jobs={len(EXAMPLE_ARRIVALS)}")
    print(f"{'Time':>4}  {'Event':<30}  Idle servers")
    for event in result["events"]:
        description = f"Job {event['job_id']} {event['event']}"
        if event["event"] == "accepted":
            allocation = event["allocated_servers"]
            unit = "server" if allocation == 1 else "servers"
            description += f" ({allocation} {unit})"
        print(f"{event['time']:4.1f}  {description:<30}  {event['idle_servers']:>12}")
    print_summary(result)


if __name__ == "__main__":
    main()
