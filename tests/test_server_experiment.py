import math
import unittest
from unittest.mock import patch

from scheduling.analysis import summarize_server_runs
from scheduling.experiments import run_policy, run_trial
from scheduling.workload import WorkloadGenerator
from tests.fixtures import make_jobs


def observation(servers, seed, blocking, execution):
    return {"servers": servers, "arrival_rate": 0.8 * servers,
            "seed": seed, "warmup_arrivals": 10,
            "measured_arrivals": 100, "blocking_probability": blocking,
            "mean_execution_time": execution}


class ServerExperimentTests(unittest.TestCase):
    def test_capacity_and_arrival_rate_change_together(self):
        jobs = make_jobs([(0, 1), (0, 1), (0, 1)])
        with patch("scheduling.experiments.WorkloadGenerator") as generator:
            generator.return_value.generate.return_value = jobs
            small = run_trial(0, 0, 3, servers=1, policy="randomized")
            generator.assert_called_with(0.8, 1.0, seed=0)
            large = run_trial(0, 0, 3, servers=4, policy="randomized")
            generator.assert_called_with(3.2, 1.0, seed=0)
        self.assertEqual(small["measured_accepted"], 1)
        self.assertEqual(large["measured_accepted"], 2)
        self.assertEqual(small["blocking_probability"], 2 / 3)
        self.assertEqual(large["blocking_probability"], 1 / 3)
        for row in (small, large):
            self.assertEqual(row["total_accepted"], row["total_completed"])
            self.assertEqual(row["final_idle_servers"], row["servers"])
            self.assertEqual(sum(row["measured_allocations"].values()), row["measured_accepted"])

    def test_100_server_trial_reproduces_existing_comparison(self):
        arrivals = WorkloadGenerator(80, seed=7).generate(110)
        previous = run_policy(arrivals, 7, "randomized", 10, policy_seed=10007)
        actual = run_trial(7, 10, 100, servers=100, policy="randomized")
        for key, value in previous.items():
            self.assertEqual(actual[key], value, key)
        self.assertEqual(actual, run_trial(7, 10, 100, servers=100, policy="randomized"))

    def test_summaries_keep_server_counts_separate(self):
        rows = [observation(50, 1, 0.4, 3), observation(100, 0, 0.1, 2),
                observation(50, 0, 0.2, 1), observation(100, 1, 0.2, 4)]
        small, large = summarize_server_runs(rows)
        self.assertEqual([small["servers"], large["servers"]], [50, 100])
        self.assertEqual(small["arrival_rate"], 40)
        self.assertEqual(large["arrival_rate"], 80)
        self.assertAlmostEqual(small["blocking_probability_mean"], 0.3)
        self.assertAlmostEqual(small["blocking_probability_sd"], 0.2 / math.sqrt(2))
        self.assertAlmostEqual(large["blocking_probability_mean"], 0.15)
        self.assertEqual(large["mean_execution_time_mean"], 3)

    def test_summaries_reject_unmatched_seeds_duplicates_and_lengths(self):
        rows = [observation(50, seed, 0.2, 1) for seed in (0, 1)]
        rows += [observation(100, seed, 0.1, 2) for seed in (0, 1)]
        for invalid in ([], rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                summarize_server_runs(invalid)
        rows[-1]["measured_arrivals"] = 200
        with self.assertRaises(ValueError):
            summarize_server_runs(rows)

    def test_trials_reject_invalid_experiment_settings(self):
        for setting in ({"servers": 0}, {"servers": True}, {"seed": None},
                        {"warmup_arrivals": -1}, {"warmup_arrivals": True},
                        {"measured_arrivals": 0}, {"measured_arrivals": 1.5}):
            arguments = {"servers": 100, "seed": 0, "warmup_arrivals": 0, "measured_arrivals": 10}
            arguments.update(setting)
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                run_trial(**arguments, policy="randomized")


if __name__ == "__main__":
    unittest.main()
