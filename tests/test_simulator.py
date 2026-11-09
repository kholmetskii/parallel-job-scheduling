import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import patch

from scheduling.allocation import optimal_allocation_probabilities, optimal_allocation_targets
from scheduling.job import Job
from scheduling.policies import GreedyPolicy, RandomizedPolicy
from scheduling.simulator import Simulator
from scheduling.workload import WorkloadGenerator
from tests.fixtures import SPEEDUPS, EXAMPLE_ARRIVALS, make_jobs


class EventLoopTests(unittest.TestCase):
    def check_conservation(self, result, servers):
        """Independently reconstruct active allocations from the event log."""
        active = {}
        accepted = rejected = completed = 0
        previous_time = 0.0
        for event in result["events"]:
            self.assertGreaterEqual(event.time, previous_time)
            previous_time = event.time
            job_id = event.job_id
            if event.kind == "accepted":
                self.assertNotIn(job_id, active)
                active[job_id] = event.allocated_servers
                accepted += 1
            elif event.kind == "completed":
                self.assertEqual(active.pop(job_id), event.allocated_servers)
                completed += 1
            else:
                self.assertEqual(event.kind, "rejected")
                self.assertEqual(event.allocated_servers, 0)
                rejected += 1
            self.assertEqual(event.idle_servers + sum(active.values()), servers)
            self.assertEqual(accepted, completed + len(active))
        self.assertFalse(active)
        self.assertEqual(result["arrivals"], accepted + rejected)
        self.assertEqual(result["accepted"], accepted)
        self.assertEqual(result["rejected"], rejected)
        self.assertEqual(result["completed"], completed)
        self.assertEqual(result["final_idle_servers"], servers)

    def test_hand_worked_six_server_trace(self):
        result = Simulator(servers=6, speedups=SPEEDUPS).run(EXAMPLE_ARRIVALS)
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
            self.assertAlmostEqual(event.time, time)
            self.assertEqual((event.kind, event.job_id,
                              event.allocated_servers, event.idle_servers),
                             (kind, job_id, allocation, idle))
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (3, 1, 3))
        self.check_conservation(result, 6)

    def test_all_simultaneous_completions_precede_arrival(self):
        result = Simulator(servers=6, speedups=SPEEDUPS).run(make_jobs([(0, 3.4), (0, 1), (1, 3.4)]))
        at_one = [(e.kind, e.job_id, e.idle_servers)
                  for e in result["events"] if e.time == 1]
        self.assertEqual(at_one, [("completed", 1, 5), ("completed", 2, 6), ("accepted", 3, 1)])
        self.assertEqual(result["rejected"], 0)
        self.check_conservation(result, 6)

    def test_simultaneous_arrivals_follow_input_order(self):
        result = Simulator(servers=6, speedups=SPEEDUPS).run(make_jobs([(0, 3.4), (0, 1), (0, 2)]))
        arrivals = [e for e in result["events"] if e.kind != "completed"]
        self.assertEqual([(e.kind, e.job_id) for e in arrivals],
                         [("accepted", 1), ("accepted", 2), ("rejected", 3)])
        self.check_conservation(result, 6)

    def test_one_server_rejection_and_release(self):
        result = Simulator(servers=1, speedups=SPEEDUPS).run(make_jobs([(0, 2), (1, 1), (2, 1)]))
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (2, 1, 2))
        self.assertEqual(result["events"][-1].time, 3)
        self.check_conservation(result, 1)

    def test_empty_input(self):
        result = Simulator(servers=6, speedups=SPEEDUPS).run([])
        self.assertEqual(result["events"], [])
        self.assertEqual(result["arrivals"], 0)
        self.check_conservation(result, 6)

    def test_rejects_invalid_inputs(self):
        for servers in [0, -1, 1.5, True]:
            with self.subTest(servers=servers), self.assertRaises(ValueError):
                Simulator(servers=servers, speedups=SPEEDUPS).run([])
        for arrivals in [[(-1, 1)], [(1, 1), (0, 1)], [(0, -1)],
                         [(float("inf"), 1)], [(0, float("nan"))]]:
            with self.subTest(arrivals=arrivals), self.assertRaises(ValueError):
                Simulator(servers=100, speedups=SPEEDUPS).run(make_jobs(arrivals))

    def test_completion_ties_use_supplied_ids_and_release_all_capacity(self):
        jobs = [Job(id=20, size=3.4, arrival_time=0),
                Job(id=3, size=1, arrival_time=0),
                Job(id=10, size=3.4, arrival_time=1)]
        result = Simulator(servers=6, speedups=SPEEDUPS).run(jobs)
        at_one = [(event.kind, event.job_id) for event in result["events"]
                  if event.time == 1]
        self.assertEqual(at_one, [("completed", 3), ("completed", 20), ("accepted", 10)])
        self.check_conservation(result, 6)

    def test_rejects_duplicate_ids_and_non_job_inputs(self):
        duplicate_ids = [Job(id=7, size=1, arrival_time=0),
                         Job(id=7, size=2, arrival_time=0)]
        with self.assertRaisesRegex(ValueError, "unique"):
            Simulator(servers=100, speedups=SPEEDUPS).run(duplicate_ids)
        with self.assertRaisesRegex(ValueError, "Job objects"):
            Simulator(servers=100, speedups=SPEEDUPS).run([(0, 1)])


class ObjectModelTests(unittest.TestCase):
    def test_shared_job_has_independent_allocations_and_completion_times(self):
        job = Job(id=7, size=5, arrival_time=2)
        jobs = [job]
        fast = Simulator(servers=3, speedups=SPEEDUPS).run(jobs)
        slow = Simulator(servers=1, speedups=SPEEDUPS).run(jobs)
        self.assertEqual((fast["events"][0].allocated_servers, fast["events"][-1].time), (3, 4))
        self.assertEqual((slow["events"][0].allocated_servers, slow["events"][-1].time), (1, 7))
        self.assertEqual((fast["final_idle_servers"], slow["final_idle_servers"]), (3, 1))
        self.assertEqual(jobs, [Job(id=7, size=5, arrival_time=2)])

    def test_job_input_cannot_be_modified(self):
        job = Job(id=7, size=5, arrival_time=2)
        for field in ("id", "size", "arrival_time"):
            with self.subTest(field=field), self.assertRaises(FrozenInstanceError):
                setattr(job, field, 10)

    def test_job_rejects_invalid_input_data(self):
        cases = {
            "id": (0, -1, True, 1.5, None, "1"),
            "size": (-1, True, None, "1", float("inf"), float("nan"), 10**400),
            "arrival_time": (-1, True, None, "1", float("inf"), float("nan"), 10**400),
        }
        for field, values in cases.items():
            for value in values:
                inputs = {"id": 1, "size": 1, "arrival_time": 0}
                inputs[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    Job(**inputs)

    def test_nonfinite_completion_is_rejected_before_reserving_servers(self):
        simulator = Simulator(servers=1, speedups=SPEEDUPS)
        job = Job(id=1, size=1e308, arrival_time=1e308)
        with self.assertRaisesRegex(ValueError, "Completion time"):
            simulator.run([job])
        self.assertEqual(simulator.pool.idle_servers, 1)
        self.assertEqual(simulator.statistics.total_accepted, 0)

    def test_reusing_simulator_starts_fresh_and_preserves_previous_result(self):
        simulator = Simulator(servers=6, speedups=SPEEDUPS)
        first = simulator.run(EXAMPLE_ARRIVALS)
        first_events = list(first["events"])
        second = simulator.run(make_jobs([(0, 3.4)]))
        self.assertEqual((second["arrivals"], second["accepted"],
                          second["rejected"], second["completed"]), (1, 1, 0, 1))
        self.assertEqual(second["events"][0].job_id, 1)
        self.assertEqual(second["final_idle_servers"], 6)
        self.assertIsNot(first["events"], second["events"])
        self.assertEqual(first["events"], first_events)
        self.assertEqual((first["arrivals"], first["accepted"], first["completed"]), (4, 3, 3))

    def test_simulator_instances_have_independent_state(self):
        first = Simulator(servers=6, speedups=SPEEDUPS)
        second = Simulator(servers=1, speedups=SPEEDUPS)
        first.run(EXAMPLE_ARRIVALS)
        second.run(make_jobs([(0, 4), (1, 1)]))
        self.assertEqual((first.current_time, first.statistics.total_accepted,
                          first.statistics.total_rejected), (2, 3, 1))
        self.assertEqual((second.current_time, second.statistics.total_accepted,
                          second.statistics.total_rejected), (4, 1, 1))
        self.assertEqual(first.pool.idle_servers, 6)
        self.assertEqual(second.pool.idle_servers, 1)


class ConfigurableSpeedupTests(unittest.TestCase):
    def test_custom_curve_controls_allocation_completion_and_ties(self):
        simulator = Simulator(servers=5, speedups=(1, 2, 3))
        result = simulator.run(make_jobs([(0, 3), (0, 2), (0, 1), (1, 3)]))
        self.assertEqual(simulator.pool.max_servers_per_job, 3)
        self.assertEqual(simulator.policy.max_servers, 3)
        accepted = [(event.job_id, event.allocated_servers)
                    for event in result["events"] if event.kind == "accepted"]
        self.assertEqual(accepted, [(1, 3), (2, 2), (4, 3)])
        at_one = [(event.kind, event.job_id) for event in result["events"]
                  if event.time == 1]
        self.assertEqual(at_one, [("completed", 1), ("completed", 2), ("accepted", 4)])
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (3, 1, 3))
        self.assertEqual(result["statistics"]["mean_execution_time"], 1)
        self.assertEqual(result["events"][-1].time, 2)
        self.assertEqual(result["final_idle_servers"], 5)

    def test_longer_curve_allows_more_than_five_servers(self):
        result = Simulator(servers=6, speedups=(1, 2, 3, 4, 5, 6)).run(make_jobs([(0, 6)]))
        self.assertEqual(result["events"][0].allocated_servers, 6)
        self.assertEqual(result["events"][-1].time, 1)
        self.assertEqual(result["statistics"]["mean_execution_time"], 1)
        self.assertEqual(result["final_idle_servers"], 6)

    def test_same_allocation_uses_each_simulators_own_speedup(self):
        fast = Simulator(servers=3, speedups=(1, 2, 3))
        slow = Simulator(servers=3, speedups=(1, 1.5, 2))
        fast_result = fast.run(make_jobs([(0, 6)]))
        slow_result = slow.run(make_jobs([(0, 6)]))
        self.assertEqual(fast_result["statistics"]["mean_execution_time"], 2)
        self.assertEqual(slow_result["statistics"]["mean_execution_time"], 3)
        self.assertEqual(fast_result, fast.run(make_jobs([(0, 6)])))

    def test_explicit_policy_keeps_its_smaller_target(self):
        result = Simulator(servers=6, policy=GreedyPolicy(max_servers=2),
                           speedups=(1, 2, 3)).run(make_jobs([(0, 3)]))
        self.assertEqual(result["events"][0].allocated_servers, 2)
        self.assertEqual(result["statistics"]["mean_execution_time"], 1.5)

    def test_curve_limit_is_checked_before_starting_a_job(self):
        simulator = Simulator(servers=6, policy=GreedyPolicy(max_servers=4),
                              speedups=(1, 2, 3))
        with self.assertRaises(ValueError):
            simulator.run(make_jobs([(0, 1)]))
        self.assertEqual(simulator.statistics.total_arrivals, 0)
        self.assertEqual(simulator.pool.idle_servers, 6)

    def test_simulator_rejects_invalid_curves(self):
        for speedups in (None, (), "1,2", (1, 1), (1, 2.1), (1, float("nan"))):
            with self.subTest(speedups=speedups), self.assertRaises(ValueError):
                Simulator(speedups=speedups, servers=100)

    def test_simulator_copies_the_callers_curve(self):
        speedups = [1, 2, 3]
        simulator = Simulator(servers=3, speedups=speedups)
        speedups[2] = 100
        self.assertEqual(simulator.pool.speedups, (1, 2, 3))
        self.assertEqual(simulator.run(make_jobs([(0, 6)]))["statistics"]["mean_execution_time"], 2)


class RandomizedModelTests(unittest.TestCase):
    def test_randomized_single_target_cases_follow_the_supplied_model(self):
        jobs = make_jobs([(10 * index, 1) for index in range(10)])
        cases = (
            (0.8, (1, 2, 3), 3),
            (0.5, (1, 1.8, 2.5, 3, 3.4), 5),
            (0.75, (1, 1.8, 2.5, 3, 3.4), 4),
        )
        for load, speedups, target in cases:
            with self.subTest(load=load, speedups=speedups):
                targets = optimal_allocation_targets(load, speedups)
                probabilities = optimal_allocation_probabilities(load, speedups)
                policy = RandomizedPolicy(targets, probabilities, seed=10000)
                with patch.object(policy.rng, "random", return_value=0.9) as draw:
                    result = Simulator(10, policy, speedups=speedups).run(
                        jobs, warmup_arrivals=2,
                    )
                    self.assertEqual(draw.call_count, len(jobs))
                self.assertEqual(result["statistics"]["allocations"][str(target)], 8)
                self.assertEqual(result["rejected"], 0)
                self.assertAlmostEqual(result["statistics"]["mean_execution_time"],
                                       1 / speedups[target - 1])

    def test_randomized_targets_and_weights_change_with_the_model(self):
        jobs = make_jobs([(10 * index, 1) for index in range(10)])
        cases = (
            (0.8, (1, 1.8, 2.5, 3, 3.4), {"3": 5, "4": 5}),
            (0.95, (1, 1.8, 2.5, 3, 3.4), {"1": 5, "2": 5}),
            (0.8, (1, 1.5), {"2": 10}),
            (0.9, (1, 1.5), {"1": 5, "2": 5}),
        )
        for load, speedups, expected in cases:
            with self.subTest(load=load, speedups=speedups):
                targets = optimal_allocation_targets(load, speedups)
                probabilities = optimal_allocation_probabilities(load, speedups)
                policy = RandomizedPolicy(targets, probabilities, seed=10000)
                with patch.object(policy.rng, "random", side_effect=[0.3, 0.8] * 5):
                    result = Simulator(10, policy, speedups=speedups).run(jobs)
                actual = {key: count for key, count in result["statistics"]["allocations"].items() if count}
                self.assertEqual(actual, expected)
                self.assertEqual(result["rejected"], 0)

    def test_generalized_model_is_reproducible_with_or_without_event_history(self):
        load, speedups = 0.9, (1, 1.5)
        jobs = WorkloadGenerator(load * 10, seed=7).generate(110)
        targets = optimal_allocation_targets(load, speedups)
        probabilities = optimal_allocation_probabilities(load, speedups)
        policy = RandomizedPolicy(targets, probabilities, seed=10007)
        simulator = Simulator(10, policy, speedups=speedups)
        expected = simulator.run(jobs, warmup_arrivals=10)
        expected.pop("events")
        for record_events in (True, False):
            simulator = Simulator(10, policy, speedups=speedups, record_events=record_events)
            actual = simulator.run(jobs, warmup_arrivals=10)
            actual.pop("events")
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
