import unittest

from scheduling.config import ModelSettings
from scheduling.policies import GreedyPolicy
from scheduling.simulation import Job, ServerPool, Simulator
from tests.fixtures import EXAMPLE_ARRIVALS


class EventLoopTests(unittest.TestCase):
    def check_conservation(self, result, servers):
        """Independently reconstruct active allocations from the event log."""
        active = {}
        accepted = rejected = completed = 0
        previous_time = 0.0
        for event in result["events"]:
            self.assertGreaterEqual(event["time"], previous_time)
            previous_time = event["time"]
            job_id = event["job_id"]
            if event["event"] == "accepted":
                self.assertNotIn(job_id, active)
                active[job_id] = event["allocated_servers"]
                accepted += 1
            elif event["event"] == "completed":
                self.assertEqual(active.pop(job_id), event["allocated_servers"])
                completed += 1
            else:
                self.assertEqual(event["event"], "rejected")
                self.assertEqual(event["allocated_servers"], 0)
                rejected += 1
            self.assertEqual(event["idle_servers"] + sum(active.values()), servers)
            self.assertEqual(accepted, completed + len(active))
        self.assertFalse(active)
        self.assertEqual(result["arrivals"], accepted + rejected)
        self.assertEqual(result["accepted"], accepted)
        self.assertEqual(result["rejected"], rejected)
        self.assertEqual(result["completed"], completed)
        self.assertEqual(result["final_idle_servers"], servers)

    def test_hand_worked_six_server_trace(self):
        result = Simulator(servers=6).run(EXAMPLE_ARRIVALS)
        expected = [
            (0.0, "accepted", 1, 5, 1),
            (0.2, "accepted", 2, 1, 0),
            (0.4, "rejected", 3, 0, 0),
            (1.0, "completed", 1, 5, 5),
            (1.0, "accepted", 4, 5, 0),
            (1.2, "completed", 2, 1, 1),
            (2.0, "completed", 4, 5, 6),
        ]
        self.assertEqual(len(result["events"]), len(expected))
        for event, (time, kind, job_id, allocation, idle) in zip(result["events"], expected):
            self.assertAlmostEqual(event["time"], time)
            self.assertEqual((event["event"], event["job_id"],
                              event["allocated_servers"], event["idle_servers"]),
                             (kind, job_id, allocation, idle))
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (3, 1, 3))
        self.check_conservation(result, 6)

    def test_all_simultaneous_completions_precede_arrival(self):
        result = Simulator(servers=6).run([(0, 3.4), (0, 1), (1, 3.4)])
        at_one = [(e["event"], e["job_id"], e["idle_servers"])
                  for e in result["events"] if e["time"] == 1]
        self.assertEqual(at_one, [("completed", 1, 5), ("completed", 2, 6), ("accepted", 3, 1)])
        self.assertEqual(result["rejected"], 0)
        self.check_conservation(result, 6)

    def test_simultaneous_arrivals_follow_input_order(self):
        result = Simulator(servers=6).run([(0, 3.4), (0, 1), (0, 2)])
        arrivals = [e for e in result["events"] if e["event"] != "completed"]
        self.assertEqual([(e["event"], e["job_id"]) for e in arrivals],
                         [("accepted", 1), ("accepted", 2), ("rejected", 3)])
        self.check_conservation(result, 6)

    def test_one_server_rejection_and_release(self):
        result = Simulator(servers=1).run([(0, 2), (1, 1), (2, 1)])
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (2, 1, 2))
        self.assertEqual(result["events"][-1]["time"], 3)
        self.check_conservation(result, 1)

    def test_empty_input(self):
        result = Simulator(servers=6).run([])
        self.assertEqual(result["events"], [])
        self.assertEqual(result["arrivals"], 0)
        self.check_conservation(result, 6)

    def test_rejects_invalid_inputs(self):
        for servers in [0, -1, 1.5, True]:
            with self.subTest(servers=servers), self.assertRaises(ValueError):
                Simulator(servers=servers).run([])
        for arrivals in [[(-1, 1)], [(1, 1), (0, 1)], [(0, -1)],
                         [(float("inf"), 1)], [(0, float("nan"))]]:
            with self.subTest(arrivals=arrivals), self.assertRaises(ValueError):
                Simulator().run(arrivals)


class ObjectModelTests(unittest.TestCase):
    def test_job_stores_timing_and_cannot_be_reallocated(self):
        job = Job(job_id=7, arrival_time=0.2, size=3.4)
        self.assertEqual(job.allocated_servers, 0)
        self.assertIsNone(job.completion_time)
        self.assertIsNone(job.start(5, speedup=3.4))
        self.assertEqual(job.allocated_servers, 5)
        self.assertAlmostEqual(job.completion_time, 1.2)
        with self.assertRaises(RuntimeError):
            job.start(1, speedup=1)
        self.assertEqual(job.allocated_servers, 5)
        self.assertAlmostEqual(job.completion_time, 1.2)

    def test_job_accepts_allocations_above_the_default_limit(self):
        job = Job(job_id=1, arrival_time=0, size=6)
        job.start(6, speedup=6)
        self.assertEqual(job.allocated_servers, 6)
        self.assertEqual(job.completion_time, 1)

    def test_job_rejects_invalid_allocations_without_starting(self):
        for allocation in (0, -1, True, 1.5):
            job = Job(job_id=1, arrival_time=0, size=1)
            with self.subTest(allocation=allocation), self.assertRaises(ValueError):
                job.start(allocation, speedup=1)
            self.assertEqual(job.allocated_servers, 0)
            self.assertIsNone(job.completion_time)

    def test_job_rejects_invalid_speedups_without_starting(self):
        for speedup in (0, -1, True, None, "2", 2 + 1j,
                        float("inf"), float("nan"), 10**400):
            job = Job(job_id=1, arrival_time=0, size=1)
            with self.subTest(speedup=speedup), self.assertRaises(ValueError):
                job.start(1, speedup=speedup)
            self.assertEqual(job.allocated_servers, 0)
            self.assertIsNone(job.completion_time)

    def test_pool_prevents_overallocation_and_overrelease(self):
        pool = ServerPool(6)
        pool.allocate(5)
        self.assertEqual((pool.idle_servers, pool.occupied_servers), (1, 5))
        for operation, count in [("allocate", 2), ("release", 6),
                                 ("allocate", 0), ("release", 0)]:
            with self.subTest(operation=operation, count=count), self.assertRaises(ValueError):
                getattr(pool, operation)(count)
            self.assertEqual((pool.idle_servers, pool.occupied_servers), (1, 5))
        pool.release(5)
        self.assertEqual((pool.idle_servers, pool.occupied_servers), (6, 0))

    def test_reusing_simulator_starts_fresh_and_preserves_previous_result(self):
        simulator = Simulator(servers=6)
        first = simulator.run(EXAMPLE_ARRIVALS)
        first_events = [event.copy() for event in first["events"]]
        second = simulator.run([(0, 3.4)])
        self.assertEqual((second["arrivals"], second["accepted"],
                          second["rejected"], second["completed"]), (1, 1, 0, 1))
        self.assertEqual(second["events"][0]["job_id"], 1)
        self.assertEqual(second["final_idle_servers"], 6)
        self.assertIsNot(first["events"], second["events"])
        self.assertEqual(first["events"], first_events)
        self.assertEqual((first["arrivals"], first["accepted"], first["completed"]), (4, 3, 3))

    def test_simulator_instances_have_independent_state(self):
        first = Simulator(servers=6)
        second = Simulator(servers=1)
        first.run(EXAMPLE_ARRIVALS)
        second.run([(0, 4), (1, 1)])
        self.assertEqual((first.current_time, first.accepted, first.rejected), (2, 3, 1))
        self.assertEqual((second.current_time, second.accepted, second.rejected), (4, 1, 1))
        self.assertEqual(first.pool.idle_servers, 6)
        self.assertEqual(second.pool.idle_servers, 1)


class ConfigurableSpeedupTests(unittest.TestCase):
    def test_custom_curve_controls_allocation_completion_and_ties(self):
        model = ModelSettings(servers=5, speedups=(1, 2, 3))
        simulator = Simulator(servers=model.servers, speedups=model.speedups)
        result = simulator.run([(0, 3), (0, 2), (0, 1), (1, 3)])
        self.assertEqual(simulator.max_servers_per_job, 3)
        self.assertEqual(simulator.policy.max_servers, 3)
        accepted = [(event["job_id"], event["allocated_servers"])
                    for event in result["events"] if event["event"] == "accepted"]
        self.assertEqual(accepted, [(1, 3), (2, 2), (4, 3)])
        at_one = [(event["event"], event["job_id"]) for event in result["events"]
                  if event["time"] == 1]
        self.assertEqual(at_one, [("completed", 1), ("completed", 2), ("accepted", 4)])
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (3, 1, 3))
        self.assertEqual(result["statistics"]["mean_execution_time"], 1)
        self.assertEqual(result["events"][-1]["time"], 2)
        self.assertEqual(result["final_idle_servers"], 5)

    def test_longer_curve_allows_more_than_five_servers(self):
        result = Simulator(servers=6, speedups=(1, 2, 3, 4, 5, 6)).run([(0, 6)])
        self.assertEqual(result["events"][0]["allocated_servers"], 6)
        self.assertEqual(result["events"][-1]["time"], 1)
        self.assertEqual(result["statistics"]["mean_execution_time"], 1)
        self.assertEqual(result["final_idle_servers"], 6)

    def test_same_allocation_uses_each_simulators_own_speedup(self):
        fast = Simulator(servers=3, speedups=(1, 2, 3))
        slow = Simulator(servers=3, speedups=(1, 1.5, 2))
        fast_result = fast.run([(0, 6)])
        slow_result = slow.run([(0, 6)])
        self.assertEqual(fast_result["statistics"]["mean_execution_time"], 2)
        self.assertEqual(slow_result["statistics"]["mean_execution_time"], 3)
        self.assertEqual(fast_result, fast.run([(0, 6)]))

    def test_explicit_policy_keeps_its_smaller_target(self):
        result = Simulator(servers=6, policy=GreedyPolicy(max_servers=2),
                           speedups=(1, 2, 3)).run([(0, 3)])
        self.assertEqual(result["events"][0]["allocated_servers"], 2)
        self.assertEqual(result["statistics"]["mean_execution_time"], 1.5)

    def test_curve_limit_is_checked_before_starting_a_job(self):
        simulator = Simulator(servers=6, policy=GreedyPolicy(max_servers=4),
                              speedups=(1, 2, 3))
        with self.assertRaises(ValueError):
            simulator.run([(0, 1)])
        self.assertEqual(simulator.arrivals_seen, 0)
        self.assertEqual(simulator.pool.idle_servers, 6)

    def test_simulator_rejects_invalid_curves(self):
        for speedups in (None, (), "1,2", (1, 1), (1, 2.1), (1, float("nan"))):
            with self.subTest(speedups=speedups), self.assertRaises(ValueError):
                Simulator(speedups=speedups)

    def test_simulator_copies_the_callers_curve(self):
        speedups = [1, 2, 3]
        simulator = Simulator(servers=3, speedups=speedups)
        speedups[2] = 100
        self.assertEqual(simulator.speedups, (1, 2, 3))
        self.assertEqual(simulator.run([(0, 6)])["statistics"]["mean_execution_time"], 2)


if __name__ == "__main__":
    unittest.main()
