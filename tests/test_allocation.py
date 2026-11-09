import math
import unittest
from fractions import Fraction
from itertools import combinations

from scheduling.allocation import optimal_allocation_probabilities, optimal_allocation_targets


SPEEDUPS = (1, 1.8, 2.5, 3, 3.4)


def feasible_vertices(load, speedups):
    """Enumerate LP (7) vertices exactly, including non-neighbouring supports."""
    vertices = {}
    for target, speedup in enumerate(speedups, start=1):
        jobs = load / speedup
        if target * jobs <= 1:
            vertices[(target,)] = jobs / load

    for lower, upper in combinations(range(1, len(speedups) + 1), 2):
        lower_speedup, upper_speedup = speedups[lower - 1], speedups[upper - 1]
        determinant = lower_speedup * upper - upper_speedup * lower
        if determinant == 0:
            continue
        # Solve service balance and full capacity as two linear equations.
        lower_jobs = (load * upper - upper_speedup) / determinant
        upper_jobs = (lower_speedup - load * lower) / determinant
        if lower_jobs > 0 and upper_jobs > 0:
            vertices[(lower, upper)] = (lower_jobs + upper_jobs) / load
    return vertices


class AllocationTargetsTests(unittest.TestCase):
    def test_baseline_uses_three_and_four(self):
        self.assertEqual(optimal_allocation_targets(0.8, SPEEDUPS), (3, 4))

    def test_light_load_and_single_server_curves_use_the_maximum(self):
        for load in (0.1, 0.5, 0.67):
            with self.subTest(load=load):
                self.assertEqual(optimal_allocation_targets(load, SPEEDUPS), (5,))
        for load in (0.01, 0.8, math.nextafter(1.0, 0.0)):
            with self.subTest(single_server_load=load):
                self.assertEqual(optimal_allocation_targets(load, (1,)), (1,))

    def test_linear_speedups_use_the_maximum_even_near_unit_load(self):
        for maximum in (2, 5, 20):
            for load in (0.1, 0.8, math.nextafter(1.0, 0.0)):
                with self.subTest(maximum=maximum, load=load):
                    self.assertEqual(
                        optimal_allocation_targets(load, tuple(range(1, maximum + 1))),
                        (maximum,),
                    )

    def test_efficiency_boundaries_use_a_single_target(self):
        for load, target in ((0.9, 2), (2.5 / 3, 3), (0.75, 4), (0.68, 5)):
            with self.subTest(load=load):
                self.assertEqual(optimal_allocation_targets(load, SPEEDUPS), (target,))

    def test_internal_boundary_tolerates_division_round_off(self):
        speedups = (1, 1.8, 2.4, 2.8)
        self.assertNotEqual(2.4 / 3, 0.8)
        self.assertEqual(optimal_allocation_targets(0.8, speedups), (3,))

    def test_loads_on_both_sides_of_boundaries_use_the_correct_neighbours(self):
        for target in range(2, 6):
            boundary = SPEEDUPS[target - 1] / target
            below = (target,) if target == 5 else (target, target + 1)
            with self.subTest(target=target):
                self.assertEqual(
                    optimal_allocation_targets(boundary - 1e-10, SPEEDUPS), below,
                )
                self.assertEqual(
                    optimal_allocation_targets(boundary + 1e-10, SPEEDUPS),
                    (target - 1, target),
                )

    def test_near_unit_load_does_not_collapse_a_linear_prefix_boundary(self):
        load = math.nextafter(1.0, 0.0)
        self.assertEqual(optimal_allocation_targets(load, SPEEDUPS), (1, 2))
        self.assertEqual(
            optimal_allocation_targets(load, (1, 2, 3, 3.8, 4.4)), (3, 4),
        )

    def test_accepts_list_curves_without_mutating_them(self):
        speedups = list(SPEEDUPS)
        self.assertEqual(optimal_allocation_targets(0.8, speedups), (3, 4))
        self.assertEqual(speedups, list(SPEEDUPS))

    def test_selected_support_attains_the_exact_lp_minimum(self):
        curves = (
            (1,), (1, 2, 3, 4, 5), SPEEDUPS,
            (1, 1.6, 2.1, 2.5), (1, 2, 3, 3.8, 4.4),
        )
        for curve in curves:
            exact_curve = tuple(Fraction(str(value)) for value in curve)
            for numerator in range(1, 10):
                load = Fraction(numerator, 10)
                with self.subTest(curve=curve, load=load):
                    vertices = feasible_vertices(load, exact_curve)
                    targets = optimal_allocation_targets(float(load), curve)
                    self.assertIn(targets, vertices)
                    self.assertEqual(vertices[targets], min(vertices.values()))


class AllocationProbabilitiesTests(unittest.TestCase):
    def assert_valid_distribution(self, load, speedups):
        targets = optimal_allocation_targets(load, speedups)
        probabilities = optimal_allocation_probabilities(load, speedups)
        self.assertEqual(len(probabilities), len(targets))
        self.assertTrue(all(math.isfinite(p) and 0 <= p <= 1 for p in probabilities))
        self.assertAlmostEqual(math.fsum(probabilities), 1.0)
        capacity = load * math.fsum(
            p * target / speedups[target - 1]
            for target, p in zip(targets, probabilities)
        )
        self.assertLessEqual(capacity, 1 + 1e-12)
        if len(targets) == 2:
            self.assertAlmostEqual(capacity, 1.0)
        return targets, probabilities

    def test_baseline_probabilities_are_five_eighths_and_three_eighths(self):
        targets, probabilities = self.assert_valid_distribution(0.8, SPEEDUPS)
        self.assertEqual(targets, (3, 4))
        for actual, expected in zip(probabilities, (0.625, 0.375)):
            self.assertAlmostEqual(actual, expected)

    def test_single_targets_have_probability_one(self):
        cases = (
            (0.8, (1,)), (0.8, (1, 2, 3, 4, 5)), (0.1, SPEEDUPS),
            (0.68, SPEEDUPS), (0.75, SPEEDUPS), (2.5 / 3, SPEEDUPS),
            (0.9, SPEEDUPS), (0.8, (1, 1.8, 2.4, 2.8)),
        )
        for load, speedups in cases:
            with self.subTest(load=load, speedups=speedups):
                self.assertEqual(optimal_allocation_probabilities(load, speedups), (1.0,))

    def test_probabilities_change_with_load_and_speedups(self):
        for load, expected in ((0.8, (0.25, 0.75)),
                               (0.9, (2 / 3, 1 / 3)),
                               (0.99, (32 / 33, 1 / 33))):
            with self.subTest(load=load):
                targets, probabilities = self.assert_valid_distribution(load, (1, 1.5))
                self.assertEqual(targets, (1, 2))
                for actual, expected_probability in zip(probabilities, expected):
                    self.assertAlmostEqual(actual, expected_probability)

    def test_probabilities_approach_one_on_both_sides_of_boundaries(self):
        for target in range(2, 6):
            boundary = SPEEDUPS[target - 1] / target
            for load in (boundary - 1e-10, boundary + 1e-10):
                with self.subTest(target=target, load=load):
                    targets, probabilities = self.assert_valid_distribution(load, SPEEDUPS)
                    self.assertGreater(probabilities[targets.index(target)], 1 - 1e-7)

    def test_near_unit_load_preserves_small_positive_probabilities(self):
        load = math.nextafter(1.0, 0.0)
        for speedups in (SPEEDUPS, (1, 2, 3, 3.8, 4.4),
                         (1, math.nextafter(1.0, math.inf))):
            with self.subTest(speedups=speedups):
                targets, probabilities = self.assert_valid_distribution(load, speedups)
                self.assertEqual(len(targets), 2)
                self.assertTrue(all(p > 0 for p in probabilities))

    def test_probabilities_accept_list_curves(self):
        self.assertEqual(
            optimal_allocation_probabilities(0.8, list(SPEEDUPS)),
            optimal_allocation_probabilities(0.8, SPEEDUPS),
        )

    def test_distribution_is_feasible_and_attains_the_exact_lp_minimum(self):
        curves = (
            (1,), (1, 2, 3, 4, 5), SPEEDUPS,
            (1, 1.6, 2.1, 2.5), (1, 2, 3, 3.8, 4.4),
        )
        loads = tuple(Fraction(n, 10) for n in range(1, 10)) + (
            Fraction(3, 4), Fraction(5, 6), Fraction(17, 25),
        )
        for curve in curves:
            exact_curve = tuple(Fraction(str(value)) for value in curve)
            for load in loads:
                with self.subTest(curve=curve, load=load):
                    targets, probabilities = self.assert_valid_distribution(float(load), curve)
                    duration = math.fsum(
                        p / curve[target - 1]
                        for target, p in zip(targets, probabilities)
                    )
                    vertices = feasible_vertices(load, exact_curve)
                    self.assertAlmostEqual(duration, float(min(vertices.values())), places=12)


if __name__ == "__main__":
    unittest.main()
