import math
import unittest

from scheduling.analysis import policy_differences
from scheduling.config import ModelSettings
from scheduling.experiments import BASELINE, run_policy, run_trial, workload_digest
from scheduling.job import Job
from scheduling.workload import WorkloadGenerator
from tests.fixtures import make_jobs


def observation(policy, seed, blocking, execution):
    return {"policy": policy, "seed": seed, "policy_seed": 10000 + seed if policy == "randomized" else None,
            "warmup_arrivals": BASELINE[0], "measured_arrivals": BASELINE[1],
            "workload_sha256": f"input-{seed}", "blocking_probability": blocking,
            "mean_execution_time": execution}


class ComparisonTests(unittest.TestCase):
    def test_supplied_model_controls_capacity_and_speedups(self):
        model = ModelSettings(servers=6, speedups=(1, 2, 3))
        result = run_policy(make_jobs([(0, 3), (0, 3)]), 0, "greedy", 0, model=model)
        self.assertEqual(result["servers"], 6)
        self.assertEqual(result["speedups"], [1, 2, 3])
        self.assertEqual(result["measured_allocations"]["3"], 2)
        self.assertEqual(result["mean_execution_time"], 1.0)
        self.assertEqual(result["final_idle_servers"], 6)

    def test_matched_trials_use_identical_inputs_and_valid_allocations(self):
        arrivals = WorkloadGenerator(80, seed=7).generate(110)
        original = arrivals.copy()
        greedy = run_policy(arrivals, 7, "greedy", 10)
        randomized = run_policy(arrivals, 7, "randomized", 10, policy_seed=10007)
        self.assertEqual(arrivals, original)
        self.assertEqual(greedy["workload_sha256"], randomized["workload_sha256"])
        self.assertEqual(randomized, run_policy(arrivals, 7, "randomized", 10, policy_seed=10007))
        for row in (greedy, randomized):
            self.assertEqual(row["measured_accepted"] + row["measured_rejected"], 100)
            self.assertEqual(sum(row["measured_allocations"].values()), row["measured_accepted"])
            self.assertEqual(row["total_accepted"], row["total_completed"])
            self.assertEqual(row["final_idle_servers"], 100)
        self.assertEqual(randomized["measured_allocations"]["5"], 0)

    def test_warmup_allocation_counts_follow_arrival_order(self):
        jobs = [Job(id=100, size=10, arrival_time=0),
                Job(id=3, size=1, arrival_time=1),
                Job(id=50, size=2, arrival_time=10),
                Job(id=1, size=1, arrival_time=11)]
        result = run_policy(jobs, 0, "greedy", 1, model=ModelSettings(servers=1))
        self.assertEqual(result["measured_arrivals"], 3)
        self.assertEqual((result["measured_accepted"], result["measured_rejected"]), (1, 2))
        self.assertEqual(result["measured_allocations"]["1"], 1)
        self.assertEqual(sum(result["measured_allocations"].values()), 1)
        self.assertEqual(result["mean_execution_time"], 2)

    def test_workload_fingerprint_changes_when_any_job_input_changes(self):
        original = workload_digest([Job(id=1, size=1, arrival_time=0)])
        for job in (Job(id=2, size=1, arrival_time=0),
                    Job(id=1, size=2, arrival_time=0),
                    Job(id=1, size=1, arrival_time=1)):
            with self.subTest(job=job):
                self.assertNotEqual(workload_digest([job]), original)

    def test_experiment_results_are_independent_of_event_history(self):
        jobs = WorkloadGenerator(80, seed=7).generate(110)
        for policy in ("greedy", "randomized"):
            with self.subTest(policy=policy):
                expected = run_policy(jobs, 7, policy, 10, policy_seed=10007)
                actual = run_policy(jobs, 7, policy, 10, policy_seed=10007, record_events=False)
                self.assertEqual(actual, expected)
                self.assertEqual(run_trial(7, 10, 100, policy=policy, record_events=False), expected)

    def test_known_paired_differences_match_seed_ids(self):
        rows = [observation("greedy", 0, 0.2, 1), observation("greedy", 1, 0.4, 3),
                observation("randomized", 1, 0.2, 4), observation("randomized", 0, 0.1, 2)]
        result = policy_differences(rows)
        self.assertEqual([row["seed"] for row in result["per_seed"]], [0, 1])
        self.assertAlmostEqual(result["summary"]["blocking_probability_mean_delta"], -0.15)
        self.assertAlmostEqual(result["summary"]["blocking_probability_delta_sd"], 0.1 / math.sqrt(2))
        self.assertEqual(result["summary"]["mean_execution_time_mean_delta"], 1)
        self.assertEqual(result["summary"]["mean_execution_time_delta_sd"], 0)

    def test_paired_differences_reject_missing_duplicate_or_changed_inputs(self):
        rows = [observation("greedy", 0, 0.2, 1), observation("greedy", 1, 0.4, 3),
                observation("randomized", 0, 0.1, 2), observation("randomized", 1, 0.2, 4)]
        with self.assertRaises(ValueError):
            policy_differences(rows[:-1])
        with self.assertRaises(ValueError):
            policy_differences(rows + [rows[0]])
        rows[-1]["workload_sha256"] = "different-inputs"
        with self.assertRaises(ValueError):
            policy_differences(rows)

    def test_comparison_requires_measured_jobs_and_a_seeded_random_policy(self):
        jobs = make_jobs([(0, 1)])
        for warmup in (-1, True, 1, 1.5):
            with self.subTest(warmup=warmup), self.assertRaises(ValueError):
                run_policy(jobs, 0, "greedy", warmup)
        with self.assertRaises(ValueError):
            run_policy(jobs, 0, "randomized", 0)
        with self.assertRaises(ValueError):
            run_policy(jobs, 0, "unknown", 0)


if __name__ == "__main__":
    unittest.main()
