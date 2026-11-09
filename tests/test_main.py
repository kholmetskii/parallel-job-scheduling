import math
import unittest
from unittest.mock import patch

import main


class ConfigurationTests(unittest.TestCase):
    def test_accepts_valid_loads_curves_and_short_runs(self):
        for speedups in ((1,), (1, 2, 3, 4, 5), main.SPEEDUPS, (1, 1.1, 1.2, 1.3)):
            for load in (0.1, 0.8, math.nextafter(1.0, 0.0)):
                with self.subTest(speedups=speedups, load=load):
                    with patch.multiple(main, SPEEDUPS=speedups, NORMALIZED_LOAD=load,
                                        WARMUP_ARRIVALS=0, MEASURED_ARRIVALS=1):
                        main.validate_configuration()

    def test_invalid_configuration_stops_before_generating_jobs(self):
        cases = {
            "SERVERS": (0, -1, 1.5, True),
            "WARMUP_ARRIVALS": (-1, 1.5, True),
            "MEASURED_ARRIVALS": (0, -1, 1.5, True),
            "NORMALIZED_LOAD": (0, 1, -0.1, float("nan"), float("inf")),
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
        with (patch.object(main, "MEAN_JOB_SIZE", 1e-320),
              patch.object(main, "WorkloadGenerator") as generator):
            with self.assertRaisesRegex(ValueError, "arrival rate"):
                main.main()
            generator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
