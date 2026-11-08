import unittest

from scheduling.config import ExperimentSettings, ModelSettings


class ModelSettingsTests(unittest.TestCase):
    def test_accepts_default_single_linear_and_rounded_speedups(self):
        ModelSettings()
        for speedups in ((1,), (1, 2, 3, 4, 5), (1, 1.8, 2.5, 3, 3.4),
                         (1, 1.1, 1.2, 1.3)):
            with self.subTest(speedups=speedups):
                ModelSettings(servers=1, normalized_load=0.5,
                              mean_job_size=2, speedups=speedups)

    def test_rejects_invalid_servers(self):
        for value in (0, -1, True, 1.5, "100", None):
            with self.subTest(servers=value), self.assertRaisesRegex(ValueError, "servers"):
                ModelSettings(servers=value)

    def test_rejects_invalid_load_or_mean_job_size(self):
        cases = {
            "normalized_load": (0, 1, -0.1, 1.1, True, None, "0.8",
                                float("nan"), float("inf"), 10**400),
            "mean_job_size": (0, -1, True, None, "1", float("nan"),
                              float("inf"), 10**400),
        }
        for name, values in cases.items():
            for value in values:
                with self.subTest(field=name, value=value), self.assertRaisesRegex(ValueError, name):
                    ModelSettings(**{name: value})

    def test_rejects_invalid_speedup_inputs(self):
        invalid = (
            (), [], None, 5, "1,2", {}, {1, 2},
            (0.5, 1), (2, 3), (1, 1), (1, 0), (1, -0.1), (1, 1.8, 1.7),
            (1, 2.1), (1, 1.8, 2.7),  # Decreasing efficiency alone is not concavity.
            (True,), (1, True), (1, "2"), (1, None), (1, 2 + 1j),
            (1, float("nan")), (1, float("inf")), (1, 10**400),
        )
        for speedups in invalid:
            with self.subTest(speedups=speedups), self.assertRaisesRegex(ValueError, "speedups"):
                ModelSettings(speedups=speedups)

    def test_copies_speedups_from_caller(self):
        speedups = [1, 1.8, 2.5]
        settings = ModelSettings(speedups=speedups)
        speedups[1] = 10
        self.assertEqual(settings.speedups, (1, 1.8, 2.5))


class ExperimentSettingsTests(unittest.TestCase):
    def test_accepts_zero_warmup_short_measurement_and_zero_thresholds(self):
        ExperimentSettings()
        for warmup in (0, 100):
            with self.subTest(warmup=warmup):
                ExperimentSettings(
                    seeds=(0, 2), policy_seed_offset=1,
                    warmup_arrivals=warmup, measured_arrivals=1, server_counts=(1,),
                    sensitivity_thresholds={"blocking_probability": 0, "mean_execution_time": 0},
                    confidence_level=0.9,
                )

    def test_rejects_invalid_workload_seeds(self):
        for seeds in (None, "01", 0, {}, {0, 1}, (), (0,), (0, 0),
                      (0, True), (0, -1), (0, 1.5), (0, "1")):
            with self.subTest(seeds=seeds), self.assertRaisesRegex(ValueError, "seeds"):
                ExperimentSettings(seeds=seeds)

    def test_rejects_invalid_policy_seed_offsets(self):
        for offset in (0, -1, True, 1.5, "10000", None):
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, "policy_seed_offset"):
                ExperimentSettings(policy_seed_offset=offset)

    def test_rejects_overlapping_random_streams(self):
        with self.assertRaisesRegex(ValueError, "workload and policy seeds"):
            ExperimentSettings(seeds=(0, 10_000), policy_seed_offset=10_000)

    def test_rejects_invalid_arrival_counts(self):
        for name in ("warmup_arrivals", "measured_arrivals"):
            invalid = [-1, True, 1.5, "100", None, float("inf")]
            if name == "measured_arrivals":
                invalid.append(0)
            for value in invalid:
                with self.subTest(field=name, value=value), self.assertRaisesRegex(ValueError, name):
                    ExperimentSettings(**{name: value})

    def test_rejects_invalid_server_counts(self):
        for counts in (None, "25", 25, {}, {25, 50}, (), (0,), (-1,),
                       (True,), (1.5,), ("25",), (25, 25)):
            with self.subTest(counts=counts), self.assertRaisesRegex(ValueError, "server_counts"):
                ExperimentSettings(server_counts=counts)

    def test_rejects_invalid_threshold_mappings(self):
        for thresholds in ([], "0.002", 0.002, {}, {"blocking_probability": 0.002},
                           {"blocking_probability": 0.002, "mean_execution_time": 0.002, "other": 0.002}):
            with self.subTest(thresholds=thresholds), self.assertRaisesRegex(ValueError, "sensitivity_thresholds"):
                ExperimentSettings(sensitivity_thresholds=thresholds)

    def test_rejects_invalid_threshold_values(self):
        for metric in ("blocking_probability", "mean_execution_time"):
            for value in (-0.001, True, None, "0.002", float("nan"), float("inf"), 10**400):
                thresholds = {"blocking_probability": 0.002, "mean_execution_time": 0.002}
                thresholds[metric] = value
                with self.subTest(metric=metric, value=value), self.assertRaisesRegex(ValueError, "sensitivity_thresholds"):
                    ExperimentSettings(sensitivity_thresholds=thresholds)

    def test_rejects_invalid_confidence_levels(self):
        for value in (0, 1, -0.1, 1.1, True, None, "0.95", float("nan"), float("inf")):
            with self.subTest(confidence_level=value), self.assertRaisesRegex(ValueError, "confidence_level"):
                ExperimentSettings(confidence_level=value)

    def test_copies_caller_collections_and_thresholds(self):
        seeds = [7, 0]
        server_counts = [200, 50]
        thresholds = {"blocking_probability": 0.005, "mean_execution_time": 0.01}
        settings = ExperimentSettings(seeds=seeds, server_counts=server_counts,
                                      sensitivity_thresholds=thresholds)
        seeds.append(7)
        server_counts[0] = 0
        thresholds["blocking_probability"] = -1
        self.assertEqual(settings.seeds, (7, 0))
        self.assertEqual(settings.server_counts, (200, 50))
        self.assertEqual(settings.sensitivity_thresholds["blocking_probability"], 0.005)

    def test_defaults_do_not_share_thresholds(self):
        first, second = ExperimentSettings(), ExperimentSettings()
        first.sensitivity_thresholds["blocking_probability"] = 1
        self.assertEqual(second.sensitivity_thresholds["blocking_probability"], 0.002)


if __name__ == "__main__":
    unittest.main()
