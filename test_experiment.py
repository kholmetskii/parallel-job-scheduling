import math
import unittest

from run_experiment import BASELINE, compare_runs, run_trial, summarize_runs


def observation(seed, blocking, execution, configuration=BASELINE):
    return {"seed": seed, "warmup_arrivals": configuration[0],
            "measured_arrivals": configuration[1],
            "blocking_probability": blocking, "mean_execution_time": execution}


class ExperimentTests(unittest.TestCase):
    def test_small_trial_preserves_measured_and_whole_run_counts(self):
        result = run_trial(seed=7, warmup_arrivals=10, measured_arrivals=100)
        self.assertEqual(result["total_arrivals"], 110)
        self.assertEqual(result["measured_arrivals"], 100)
        self.assertEqual(result["measured_accepted"] + result["measured_rejected"], 100)
        self.assertEqual(result["total_accepted"], result["total_completed"])
        self.assertEqual(result["total_accepted"] + result["total_rejected"], 110)
        self.assertEqual(result["final_idle_servers"], 100)
        self.assertAlmostEqual(result["blocking_probability"], result["measured_rejected"] / 100)
        self.assertAlmostEqual(result["mean_execution_time"],
                               result["measured_total_execution_time"] / result["measured_accepted"])

    def test_rejects_invalid_trial_lengths(self):
        for value in (-1, 1.5, True):
            with self.subTest(warmup=value), self.assertRaises(ValueError):
                run_trial(0, value, 100)
        for value in (0, -1, 1.5, True):
            with self.subTest(measured=value), self.assertRaises(ValueError):
                run_trial(0, 10, value)

    def test_summary_uses_known_means_and_sample_standard_deviations(self):
        rows = [observation(0, 0.2, 1.0), observation(1, 0.4, 3.0)]
        summary = summarize_runs(rows)[0]
        self.assertEqual(summary["runs"], 2)
        self.assertAlmostEqual(summary["blocking_probability_mean"], 0.3)
        self.assertAlmostEqual(summary["blocking_probability_sd"], math.sqrt(0.02))
        self.assertAlmostEqual(summary["mean_execution_time_mean"], 2.0)
        self.assertAlmostEqual(summary["mean_execution_time_sd"], math.sqrt(2.0))

    def test_summary_rejects_duplicate_seeds_and_insufficient_observations(self):
        row = observation(0, 0.2, 1.0)
        for rows in ([row, row], [row], [row, observation(1, None, 2.0)]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                summarize_runs(rows)

    def test_paired_comparison_matches_seed_ids_instead_of_row_order(self):
        variant = (1000, 100_000)
        rows = [observation(0, 0.2, 1.0), observation(1, 0.3, 2.0),
                observation(1, 0.4, 2.3, variant), observation(0, 0.21, 1.1, variant)]
        comparison = compare_runs(rows)[0]
        self.assertAlmostEqual(comparison["blocking_probability_mean_delta"], 0.055)
        self.assertAlmostEqual(comparison["blocking_probability_delta_sd"], 0.09 / math.sqrt(2))
        self.assertAlmostEqual(comparison["mean_execution_time_mean_delta"], 0.2)
        self.assertAlmostEqual(comparison["mean_execution_time_delta_sd"], 0.2 / math.sqrt(2))

    def test_paired_comparison_rejects_different_seed_sets(self):
        rows = [observation(0, 0.2, 1.0), observation(1, 0.3, 2.0),
                observation(0, 0.21, 1.1, (1000, 100_000)),
                observation(2, 0.4, 2.3, (1000, 100_000))]
        with self.assertRaises(ValueError):
            compare_runs(rows)


if __name__ == "__main__":
    unittest.main()
