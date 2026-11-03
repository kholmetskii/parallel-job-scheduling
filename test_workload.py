import math
import random
import unittest

from simulation import Simulator
from workload import WorkloadGenerator


class WorkloadGeneratorTests(unittest.TestCase):
    def test_requested_count_and_ordered_finite_values(self):
        arrivals = WorkloadGenerator(arrival_rate=80, seed=42).generate(1000)
        self.assertEqual(len(arrivals), 1000)
        self.assertGreater(arrivals[0][0], 0)
        previous_time = 0.0
        for arrival_time, size in arrivals:
            self.assertTrue(math.isfinite(arrival_time))
            self.assertGreaterEqual(arrival_time, previous_time)
            self.assertTrue(math.isfinite(size))
            self.assertGreaterEqual(size, 0)
            previous_time = arrival_time

    def test_fresh_generators_with_same_seed_reproduce_workload(self):
        first = WorkloadGenerator(arrival_rate=80, seed=42).generate(100)
        second = WorkloadGenerator(arrival_rate=80, seed=42).generate(100)
        self.assertEqual(first, second)

    def test_different_seeds_change_workload(self):
        first = WorkloadGenerator(arrival_rate=80, seed=42).generate(100)
        second = WorkloadGenerator(arrival_rate=80, seed=43).generate(100)
        self.assertNotEqual(first, second)

    def test_does_not_change_global_random_state(self):
        previous_state = random.getstate()
        WorkloadGenerator(arrival_rate=80, seed=42).generate(100)
        self.assertEqual(random.getstate(), previous_state)

    def test_sample_means_and_tails_match_exponential_settings(self):
        arrival_rate = 8.0
        mean_job_size = 2.5
        arrivals = WorkloadGenerator(
            arrival_rate=arrival_rate, mean_job_size=mean_job_size, seed=42,
        ).generate(20_000)
        gaps = []
        sizes = []
        previous_time = 0.0
        for arrival_time, size in arrivals:
            gaps.append(arrival_time - previous_time)
            sizes.append(size)
            previous_time = arrival_time

        # Fixed seed and broad tolerances provide a deterministic sanity check.
        for samples, expected_mean in ((gaps, 1.0 / arrival_rate),
                                       (sizes, mean_job_size)):
            with self.subTest(expected_mean=expected_mean):
                sample_mean = sum(samples) / len(samples)
                self.assertAlmostEqual(sample_mean, expected_mean,
                                       delta=0.03 * expected_mean)
                tail_fraction = sum(value > expected_mean for value in samples) / len(samples)
                self.assertAlmostEqual(tail_fraction, math.exp(-1), delta=0.02)

    def test_zero_jobs_returns_empty_workload(self):
        self.assertEqual(WorkloadGenerator(arrival_rate=80, seed=42).generate(0), [])

    def test_rejects_invalid_settings(self):
        for value in (0, -1, float("inf"), float("nan")):
            with self.subTest(arrival_rate=value), self.assertRaises(ValueError):
                WorkloadGenerator(arrival_rate=value)
            with self.subTest(mean_job_size=value), self.assertRaises(ValueError):
                WorkloadGenerator(arrival_rate=80, mean_job_size=value)
        for seed in (True, 1.5, "42"):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                WorkloadGenerator(arrival_rate=80, seed=seed)

    def test_rejects_invalid_job_counts(self):
        workload = WorkloadGenerator(arrival_rate=80, seed=42)
        for count in (-1, 1.5, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                workload.generate(count)

    def test_random_workload_runs_in_simulator_and_can_be_replayed(self):
        arrivals = WorkloadGenerator(arrival_rate=80, seed=42).generate(1000)
        result = Simulator(servers=100).run(arrivals)
        self.assertEqual(result["arrivals"], 1000)
        self.assertEqual(result["accepted"] + result["rejected"], 1000)
        self.assertGreater(result["accepted"], 0)
        self.assertEqual(result["completed"], result["accepted"])
        self.assertEqual(result["final_idle_servers"], 100)
        self.assertEqual(result, Simulator(servers=100).run(arrivals))


if __name__ == "__main__":
    unittest.main()
