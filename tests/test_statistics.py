import unittest

from scheduling.job import Job
from scheduling.policies import GreedyPolicy, RandomizedPolicy
from scheduling.simulator import Simulator
from scheduling.statistics import Statistics
from scheduling.workload import WorkloadGenerator
from tests.fixtures import SPEEDUPS, EXAMPLE_ARRIVALS, make_jobs


class StatisticsTests(unittest.TestCase):
    def test_warmup_allocation_counts_follow_arrival_order(self):
        jobs = [Job(id=100, size=10, arrival_time=0),
                Job(id=3, size=1, arrival_time=1),
                Job(id=50, size=2, arrival_time=10),
                Job(id=1, size=1, arrival_time=11)]
        result = Simulator(servers=1, speedups=SPEEDUPS).run(jobs, warmup_arrivals=1)
        statistics = result["statistics"]
        self.assertEqual(statistics["arrivals"], 3)
        self.assertEqual((statistics["accepted"], statistics["rejected"]), (1, 2))
        self.assertEqual(statistics["allocations"]["1"], 1)
        self.assertEqual(sum(statistics["allocations"].values()), 1)
        self.assertEqual(statistics["mean_execution_time"], 2)

    def test_hand_worked_example_has_known_metrics(self):
        statistics = Simulator(servers=6, speedups=SPEEDUPS).run(EXAMPLE_ARRIVALS)["statistics"]
        self.assertEqual(statistics["warmup_arrivals"], 0)
        self.assertEqual(statistics["arrivals"], 4)
        self.assertEqual(statistics["accepted"], 3)
        self.assertEqual(statistics["rejected"], 1)
        self.assertAlmostEqual(statistics["total_execution_time"], 3.0)
        self.assertAlmostEqual(statistics["blocking_probability"], 0.25)
        self.assertAlmostEqual(statistics["mean_execution_time"], 1.0)

    def test_warmup_preserves_capacity_and_excludes_jobs_by_arrival(self):
        # Job 1 keeps the server until time 10, after measurement has started.
        arrivals = make_jobs([(0, 10), (1, 1), (10, 2), (11, 1)])
        simulator = Simulator(servers=1, speedups=SPEEDUPS)
        result = simulator.run(arrivals, warmup_arrivals=1)
        statistics = result["statistics"]
        self.assertEqual((result["arrivals"], result["accepted"],
                          result["rejected"], result["completed"]), (4, 2, 2, 2))
        self.assertEqual(statistics["arrivals"], 3)
        self.assertEqual(statistics["accepted"], 1)
        self.assertEqual(statistics["rejected"], 2)
        self.assertAlmostEqual(statistics["blocking_probability"], 2 / 3)
        self.assertAlmostEqual(statistics["total_execution_time"], 2.0)
        self.assertAlmostEqual(statistics["mean_execution_time"], 2.0)
        self.assertEqual(result["events"], Simulator(servers=1, speedups=SPEEDUPS).run(arrivals)["events"])
        self.assertEqual(result["final_idle_servers"], 1)

    def test_full_duration_counts_when_completion_follows_final_arrival(self):
        result = Simulator(servers=1, speedups=SPEEDUPS).run(make_jobs([(0, 2), (3, 7)]), warmup_arrivals=1)
        self.assertEqual(result["events"][-1].time, 10)
        self.assertEqual(result["completed"], 2)
        self.assertAlmostEqual(result["statistics"]["mean_execution_time"], 7.0)
        self.assertAlmostEqual(result["statistics"]["total_execution_time"], 7.0)

    def test_all_measured_arrivals_rejected(self):
        # The cutoff can split arrivals that share a timestamp.
        result = Simulator(servers=1, speedups=SPEEDUPS).run(make_jobs([(0, 10), (0, 1), (0, 1)]), warmup_arrivals=1)
        statistics = result["statistics"]
        self.assertEqual(statistics["arrivals"], 2)
        self.assertEqual(statistics["accepted"], 0)
        self.assertEqual(statistics["rejected"], 2)
        self.assertEqual(statistics["blocking_probability"], 1.0)
        self.assertIsNone(statistics["mean_execution_time"])
        self.assertEqual(statistics["total_execution_time"], 0.0)

    def test_empty_measurements_return_none_metrics(self):
        for arrivals, warmup in (([], 0), (EXAMPLE_ARRIVALS, 4), (EXAMPLE_ARRIVALS, 10)):
            with self.subTest(warmup=warmup):
                result = Simulator(servers=6, speedups=SPEEDUPS).run(arrivals, warmup_arrivals=warmup)
                statistics = result["statistics"]
                self.assertEqual(statistics["arrivals"], 0)
                self.assertEqual(statistics["accepted"], 0)
                self.assertEqual(statistics["rejected"], 0)
                self.assertIsNone(statistics["blocking_probability"])
                self.assertIsNone(statistics["mean_execution_time"])
                self.assertEqual(result["completed"], result["accepted"])
                self.assertEqual(result["final_idle_servers"], 6)

    def test_rejects_invalid_warmup_counts(self):
        for warmup in (-1, 1.5, True, None, "1"):
            with self.subTest(warmup=warmup), self.assertRaises(ValueError):
                Simulator(servers=100, speedups=SPEEDUPS).run([], warmup_arrivals=warmup)

    def test_zero_duration_is_a_valid_measured_execution_time(self):
        statistics = Simulator(servers=1, speedups=SPEEDUPS).run(make_jobs([(0, 0)]))["statistics"]
        self.assertEqual(statistics["accepted"], 1)
        self.assertEqual(statistics["blocking_probability"], 0.0)
        self.assertEqual(statistics["mean_execution_time"], 0.0)

    def test_reusing_simulator_resets_statistics_and_warmup(self):
        simulator = Simulator(servers=6, speedups=SPEEDUPS)
        first = simulator.run(EXAMPLE_ARRIVALS, warmup_arrivals=2)
        original_statistics = first["statistics"].copy()
        second = simulator.run(make_jobs([(0, 6.8)]))
        self.assertEqual(second["statistics"]["warmup_arrivals"], 0)
        self.assertEqual(second["statistics"]["arrivals"], 1)
        self.assertEqual(second["statistics"]["accepted"], 1)
        self.assertAlmostEqual(second["statistics"]["mean_execution_time"], 2.0)
        self.assertIsNot(first["statistics"], second["statistics"])
        self.assertEqual(first["statistics"], original_statistics)
        self.assertEqual(first["statistics"]["arrivals"], 2)
        self.assertAlmostEqual(first["statistics"]["blocking_probability"], 0.5)

    def test_random_metrics_match_independent_event_log_calculation(self):
        arrivals = WorkloadGenerator(arrival_rate=80, seed=42).generate(1000)
        warmup = 100
        result = Simulator(servers=100, speedups=SPEEDUPS).run(iter(arrivals), warmup_arrivals=warmup)
        accepted_times = {}
        rejected = 0
        durations = []
        measured_ids = {job.id for job in arrivals[warmup:]}
        for event in result["events"]:
            if event.job_id not in measured_ids:
                continue
            if event.kind == "accepted":
                accepted_times[event.job_id] = event.time
            elif event.kind == "rejected":
                rejected += 1
            elif event.kind == "completed":
                durations.append(event.time - accepted_times.pop(event.job_id))
        self.assertFalse(accepted_times)
        statistics = result["statistics"]
        self.assertEqual(statistics["arrivals"], 900)
        self.assertEqual(statistics["accepted"], len(durations))
        self.assertEqual(statistics["rejected"], rejected)
        self.assertAlmostEqual(statistics["blocking_probability"], rejected / 900)
        self.assertAlmostEqual(statistics["total_execution_time"], sum(durations))
        self.assertAlmostEqual(statistics["mean_execution_time"], sum(durations) / len(durations))

    def test_warmup_uses_arrival_order_with_nonconsecutive_ids(self):
        jobs = [Job(id=100, size=10, arrival_time=0),
                Job(id=3, size=1, arrival_time=1),
                Job(id=50, size=2, arrival_time=10),
                Job(id=1, size=1, arrival_time=11)]
        result = Simulator(servers=1, speedups=SPEEDUPS).run(iter(jobs), warmup_arrivals=1)
        statistics = result["statistics"]
        self.assertEqual((statistics["arrivals"], statistics["accepted"], statistics["rejected"]),
                         (3, 1, 2))
        self.assertEqual(statistics["mean_execution_time"], 2)
        self.assertEqual(statistics["blocking_probability"], 2 / 3)
        self.assertEqual([event.job_id for event in result["events"]
                          if event.kind == "accepted"], [100, 50])

    def test_totals_include_warmup_while_measurements_follow_arrival_order(self):
        statistics = Statistics(warmup_arrivals=2, max_servers_per_job=3)
        statistics.record_arrival(3, 10)
        statistics.record_arrival(0, None)
        statistics.record_completion()
        statistics.record_arrival(2, 4)
        statistics.record_arrival(0, None)
        statistics.record_arrival(1, 0)
        statistics.record_completion()
        statistics.record_completion()
        self.assertEqual((statistics.total_arrivals, statistics.total_accepted,
                          statistics.total_rejected, statistics.total_completed), (5, 3, 2, 3))
        summary = statistics.summary()
        self.assertEqual((summary["arrivals"], summary["accepted"], summary["rejected"]), (3, 2, 1))
        self.assertEqual(summary["total_execution_time"], 4)
        self.assertEqual(summary["mean_execution_time"], 2)
        self.assertEqual(summary["blocking_probability"], 1 / 3)
        self.assertEqual(summary["allocations"], {"1": 1, "2": 1, "3": 0})

    def test_allocation_summaries_remain_independent_snapshots(self):
        statistics = Statistics(max_servers_per_job=2)
        statistics.record_arrival(1, 2)
        first = statistics.summary()
        statistics.record_arrival(2, 3)
        self.assertEqual(first["allocations"], {"1": 1, "2": 0})
        first["allocations"]["1"] = 100
        self.assertEqual(statistics.summary()["allocations"], {"1": 1, "2": 1})

    def test_disabling_event_history_preserves_all_measurements_and_replay(self):
        jobs = make_jobs([(0, 0), (0, 3.4), (0, 1), (0, 2), (1, 0), (1, 3.4)])
        for name in ("greedy", "randomized"):
            with self.subTest(policy=name):
                policy = GreedyPolicy() if name == "greedy" else RandomizedPolicy((3, 4), (0.625, 0.375), seed=10007)
                expected = Simulator(servers=6, policy=policy, speedups=SPEEDUPS).run(jobs, warmup_arrivals=2)
                quiet = Simulator(servers=6, policy=policy, record_events=False, speedups=SPEEDUPS)
                actual = quiet.run(jobs, warmup_arrivals=2)
                self.assertTrue(expected.pop("events"))
                self.assertEqual(actual.pop("events"), [])
                self.assertEqual(actual, expected)
                replay = quiet.run(jobs, warmup_arrivals=2)
                self.assertEqual(replay.pop("events"), [])
                self.assertEqual(replay, expected)


if __name__ == "__main__":
    unittest.main()
