import random
import unittest
from unittest.mock import patch

from scheduling.policies import GreedyPolicy, RandomizedPolicy
from scheduling.simulator import Simulator
from tests.fixtures import SPEEDUPS, make_jobs


class PolicyTests(unittest.TestCase):
    def test_greedy_uses_capacity_up_to_its_maximum(self):
        policy = GreedyPolicy()
        for idle in range(10):
            self.assertEqual(policy.choose_allocation(idle), min(5, idle))
        self.assertEqual(GreedyPolicy(max_servers=2).choose_allocation(10), 2)

    def test_random_target_switches_at_the_probability_boundary(self):
        policy = RandomizedPolicy((3, 4), (0.625, 0.375), seed=42)
        with patch.object(policy.rng, "random", side_effect=[0.0, 0.624999, 0.625, 0.999]):
            self.assertEqual([policy.choose_allocation(10) for _ in range(4)], [3, 3, 4, 4])

    def test_random_targets_are_capped_by_idle_capacity(self):
        policy = RandomizedPolicy((3, 4), (0.625, 0.375), seed=42)
        for draw, target in ((0.1, 3), (0.9, 4)):
            with patch.object(policy.rng, "random", return_value=draw):
                for idle in range(6):
                    self.assertEqual(policy.choose_allocation(idle), min(target, idle))

    def test_blocked_arrivals_also_consume_a_target_draw(self):
        policy = RandomizedPolicy((3, 4), (0.625, 0.375), seed=42)
        with patch.object(policy.rng, "random", side_effect=[0.1, 0.9]) as draw:
            self.assertEqual(policy.choose_allocation(0), 0)
            self.assertEqual(policy.choose_allocation(10), 4)
            self.assertEqual(draw.call_count, 2)

    def test_target_frequencies_match_the_configured_probability(self):
        policy = RandomizedPolicy((3, 4), (0.625, 0.375), seed=42)
        targets = [policy.choose_allocation(10) for _ in range(10_000)]
        self.assertEqual(set(targets), {3, 4})
        self.assertAlmostEqual(targets.count(3) / len(targets), 0.625, delta=0.02)

    def test_policy_uses_local_random_state(self):
        state = random.getstate()
        policy = RandomizedPolicy((3, 4), (0.625, 0.375), seed=42)
        for _ in range(100):
            policy.choose_allocation(10)
        policy.reset()
        self.assertEqual(random.getstate(), state)

    def test_reused_simulator_restarts_the_seeded_policy(self):
        arrivals = make_jobs([(time, 3.0) for time in range(20)])
        simulator = Simulator(servers=100, policy=RandomizedPolicy((3, 4), (0.625, 0.375), seed=42), speedups=SPEEDUPS)
        first = simulator.run(arrivals)
        self.assertEqual(first, simulator.run(arrivals))
        self.assertEqual(first, Simulator(100, RandomizedPolicy((3, 4), (0.625, 0.375), seed=42), speedups=SPEEDUPS).run(arrivals))
        self.assertNotEqual(first, Simulator(100, RandomizedPolicy((3, 4), (0.625, 0.375), seed=43), speedups=SPEEDUPS).run(arrivals))

    def test_partial_allocation_rejection_and_completion_order(self):
        policy = RandomizedPolicy((3, 4), (0.625, 0.375), seed=42)
        with patch.object(policy.rng, "random", side_effect=[0.1, 0.9, 0.1, 0.9]):
            result = Simulator(5, policy, speedups=SPEEDUPS).run(make_jobs([(0, 2.5), (0.1, 1.8), (0.2, 1), (1, 2.5)]))
        events = result["events"]
        self.assertEqual([(e.job_id, e.allocated_servers)
                          for e in events if e.kind == "accepted"], [(1, 3), (2, 2), (4, 3)])
        self.assertEqual(result["rejected"], 1)
        self.assertEqual([(e.kind, e.job_id) for e in events if e.time == 1],
                         [("completed", 1), ("accepted", 4)])
        self.assertEqual(result["final_idle_servers"], 5)
        self.assertAlmostEqual(result["statistics"]["mean_execution_time"], 1.0)

    def test_simulator_rejects_allocations_outside_the_model(self):
        class InvalidPolicy(GreedyPolicy):
            def __init__(self, allocation):
                super().__init__()
                self.allocation = allocation

            def choose_allocation(self, idle_servers):
                return self.allocation

        for allocation in (-1, 0, True, 6):
            with self.subTest(allocation=allocation), self.assertRaises(ValueError):
                Simulator(servers=5, policy=InvalidPolicy(allocation), speedups=SPEEDUPS).run(make_jobs([(0, 1)]))

    def test_three_target_distribution_uses_its_configured_boundaries(self):
        policy = RandomizedPolicy((1, 2, 5), (0.2, 0.3, 0.5), seed=42)
        draws = (0.0, 0.199999, 0.2, 0.499999, 0.5, 0.999)
        with patch.object(policy.rng, "random", side_effect=draws) as draw:
            self.assertEqual([policy.choose_allocation(10) for _ in draws], [1, 1, 2, 2, 5, 5])
            self.assertEqual(draw.call_count, len(draws))

    def test_single_and_zero_weight_targets_still_consume_one_draw(self):
        for targets, probabilities, expected in (
            ((5,), (1,), 5), ((1, 3, 5), (0, 1, 0), 3),
        ):
            with self.subTest(targets=targets):
                policy = RandomizedPolicy(targets, probabilities, seed=42)
                with patch.object(policy.rng, "random", side_effect=(0.0, 0.9, 0.5)) as draw:
                    self.assertEqual(policy.choose_allocation(0), 0)
                    self.assertEqual(policy.choose_allocation(10), expected)
                    self.assertEqual(policy.choose_allocation(2), 2)
                    self.assertEqual(draw.call_count, 3)

    def test_distribution_copies_caller_inputs_and_replays_after_reset(self):
        targets, probabilities = [1, 4], [0.25, 0.75]
        policy = RandomizedPolicy(targets, probabilities, seed=42)
        targets[0], probabilities[0] = 9, 1
        self.assertEqual(policy.targets, (1, 4))
        self.assertEqual(policy.probabilities, (0.25, 0.75))
        first = [policy.choose_allocation(10) for _ in range(100)]
        policy.reset()
        self.assertEqual(first, [policy.choose_allocation(10) for _ in range(100)])

if __name__ == "__main__":
    unittest.main()
