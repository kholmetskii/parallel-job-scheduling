import math
import unittest
from unittest.mock import patch

import main


class ConfigurationTests(unittest.TestCase):
    def test_accepts_valid_loads_curves_and_short_runs(self):
        cases = (
            (100, 0, 0.9, 0.1),
            (100, 0, 0.2, 0.8),
            (100, 0, 1 - math.nextafter(1.0, 0.0), math.nextafter(1.0, 0.0)),
            (100, 1 / 2, 0.1, 0.99),
            (400, 1 / 2, 0.1, 0.995),
            (8, 2 / 3, 0.1, 0.975),
            (64, 2 / 3, 0.1, 0.99375),
        )
        for speedups in ((1,), (1, 2, 3, 4, 5), main.SPEEDUPS, (1, 1.1, 1.2, 1.3)):
            for servers, alpha, beta, expected in cases:
                with self.subTest(speedups=speedups, servers=servers, alpha=alpha, beta=beta):
                    with patch.multiple(main, SPEEDUPS=speedups, SERVERS=servers,
                                        ALPHA=alpha, BETA=beta,
                                        WARMUP_ARRIVALS=0, MEASURED_ARRIVALS=1):
                        self.assertIsNone(main.validate_configuration())
                    self.assertAlmostEqual(main.normalized_load(servers, alpha, beta), expected)

    def test_invalid_configuration_stops_before_generating_jobs(self):
        cases = {
            "SERVERS": (0, -1, 1.5, True),
            "WARMUP_ARRIVALS": (-1, 1.5, True),
            "MEASURED_ARRIVALS": (0, -1, 1.5, True),
            "ALPHA": (-0.1, float("nan"), float("inf")),
            "BETA": (0, -0.1, float("nan"), float("inf")),
            "MEAN_JOB_SIZE": (0, -1, float("nan"), float("inf")),
            "SPEEDUPS": ((), (2,), (1, 1), (1, -1), (1, 2.1), (1, 1.8, 2.7),
                        (1, float("nan")), (1, float("inf"))),
        }
        for name, values in cases.items():
            for value in values:
                with self.subTest(setting=name, value=value):
                    with (patch.object(main, name, value),
                          patch.object(main, "WorkloadGenerator") as generator):
                        with self.assertRaisesRegex(ValueError, name):
                            main.main()
                        generator.assert_not_called()
        for beta in (1, 1.1):
            with self.subTest(beta=beta):
                with (patch.multiple(main, ALPHA=0, BETA=beta),
                      patch.object(main, "WorkloadGenerator") as generator):
                    with self.assertRaisesRegex(ValueError, "normalized load"):
                        main.main()
                    generator.assert_not_called()
        with (patch.object(main, "MEAN_JOB_SIZE", 1e-320),
              patch.object(main, "WorkloadGenerator") as generator):
            with self.assertRaisesRegex(ValueError, "arrival rate"):
                main.main()
            generator.assert_not_called()

    def test_main_uses_derived_load_and_mean_size_for_workload_allocation_and_benchmark(self):
        with (patch.multiple(main, SERVERS=400, ALPHA=1 / 2, BETA=0.1,
                             MEAN_JOB_SIZE=2.0,
                             WARMUP_ARRIVALS=0, MEASURED_ARRIVALS=1),
              patch.object(main, "WorkloadGenerator", wraps=main.WorkloadGenerator) as generator,
              patch.object(main, "Simulator", wraps=main.Simulator) as simulator,
              patch.object(main, "optimal_mean_execution_time",
                           wraps=main.optimal_mean_execution_time) as benchmark,
              patch("builtins.print") as output):
            main.main()
            generator.assert_called_once_with(199.0, main.MEAN_JOB_SIZE, seed=main.WORKLOAD_SEED)
            policy = simulator.call_args.kwargs["policy"]
            self.assertEqual(policy.targets, (1, 2))
            self.assertAlmostEqual(policy.probabilities[1], 9 / 199)
            benchmark.assert_called_once_with(0.995, main.SPEEDUPS, 2.0)
            output.assert_any_call("Theoretical mean execution-time benchmark: 1.959799")


if __name__ == "__main__":
    unittest.main()
