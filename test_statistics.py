import unittest

from run_fixed import EXAMPLE_ARRIVALS
from simulation import Simulator
from workload import WorkloadGenerator


class StatisticsTests(unittest.TestCase):
    def test_hand_worked_example_has_known_metrics(self):
        statistics = Simulator(servers=6).run(EXAMPLE_ARRIVALS)["statistics"]
        self.assertEqual(statistics["warmup_arrivals"], 0)
        self.assertEqual(statistics["arrivals"], 4)
        self.assertEqual(statistics["accepted"], 3)
        self.assertEqual(statistics["rejected"], 1)
        self.assertAlmostEqual(statistics["total_execution_time"], 3.0)
        self.assertAlmostEqual(statistics["blocking_probability"], 0.25)
        self.assertAlmostEqual(statistics["mean_execution_time"], 1.0)

    def test_warmup_preserves_capacity_and_excludes_jobs_by_arrival(self):
        # Job 1 keeps the server until time 10, after measurement has started.
        arrivals = [(0, 10), (1, 1), (10, 2), (11, 1)]
        simulator = Simulator(servers=1)
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
        self.assertEqual(result["events"], Simulator(servers=1).run(arrivals)["events"])
        self.assertEqual(result["final_idle_servers"], 1)

    def test_full_duration_counts_when_completion_follows_final_arrival(self):
        result = Simulator(servers=1).run([(0, 2), (3, 7)], warmup_arrivals=1)
        self.assertEqual(result["events"][-1]["time"], 10)
        self.assertEqual(result["completed"], 2)
        self.assertAlmostEqual(result["statistics"]["mean_execution_time"], 7.0)
        self.assertAlmostEqual(result["statistics"]["total_execution_time"], 7.0)

    def test_all_measured_arrivals_rejected(self):
        # The cutoff can split arrivals that share a timestamp.
        result = Simulator(servers=1).run([(0, 10), (0, 1), (0, 1)], warmup_arrivals=1)
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
                result = Simulator(servers=6).run(arrivals, warmup_arrivals=warmup)
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
                Simulator().run([], warmup_arrivals=warmup)

    def test_zero_duration_is_a_valid_measured_execution_time(self):
        statistics = Simulator(servers=1).run([(0, 0)])["statistics"]
        self.assertEqual(statistics["accepted"], 1)
        self.assertEqual(statistics["blocking_probability"], 0.0)
        self.assertEqual(statistics["mean_execution_time"], 0.0)

    def test_reusing_simulator_resets_statistics_and_warmup(self):
        simulator = Simulator(servers=6)
        first = simulator.run(EXAMPLE_ARRIVALS, warmup_arrivals=2)
        original_statistics = first["statistics"].copy()
        second = simulator.run([(0, 6.8)])
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
        result = Simulator(servers=100).run(iter(arrivals), warmup_arrivals=warmup)
        accepted_times = {}
        rejected = 0
        durations = []
        for event in result["events"]:
            if event["job_id"] <= warmup:
                continue
            if event["event"] == "accepted":
                accepted_times[event["job_id"]] = event["time"]
            elif event["event"] == "rejected":
                rejected += 1
            elif event["event"] == "completed":
                durations.append(event["time"] - accepted_times.pop(event["job_id"]))
        self.assertFalse(accepted_times)
        statistics = result["statistics"]
        self.assertEqual(statistics["arrivals"], 900)
        self.assertEqual(statistics["accepted"], len(durations))
        self.assertEqual(statistics["rejected"], rejected)
        self.assertAlmostEqual(statistics["blocking_probability"], rejected / 900)
        self.assertAlmostEqual(statistics["total_execution_time"], sum(durations))
        self.assertAlmostEqual(statistics["mean_execution_time"], sum(durations) / len(durations))


if __name__ == "__main__":
    unittest.main()
