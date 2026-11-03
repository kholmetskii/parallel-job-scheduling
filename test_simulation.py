import unittest

from simulation import EXAMPLE_ARRIVALS, simulate


class EventLoopTests(unittest.TestCase):
    def check_conservation(self, result, servers):
        """Independently reconstruct active allocations from the event log."""
        active = {}
        accepted = rejected = completed = 0
        previous_time = 0.0
        for event in result["events"]:
            self.assertGreaterEqual(event["time"], previous_time)
            previous_time = event["time"]
            job_id = event["job_id"]
            if event["event"] == "accepted":
                self.assertNotIn(job_id, active)
                active[job_id] = event["allocated_servers"]
                accepted += 1
            elif event["event"] == "completed":
                self.assertEqual(active.pop(job_id), event["allocated_servers"])
                completed += 1
            else:
                self.assertEqual(event["event"], "rejected")
                self.assertEqual(event["allocated_servers"], 0)
                rejected += 1
            self.assertEqual(event["idle_servers"] + sum(active.values()), servers)
            self.assertEqual(accepted, completed + len(active))
        self.assertFalse(active)
        self.assertEqual(result["arrivals"], accepted + rejected)
        self.assertEqual(result["accepted"], accepted)
        self.assertEqual(result["rejected"], rejected)
        self.assertEqual(result["completed"], completed)
        self.assertEqual(result["final_idle_servers"], servers)

    def test_hand_worked_six_server_trace(self):
        result = simulate(EXAMPLE_ARRIVALS, servers=6)
        expected = [
            (0.0, "accepted", 1, 5, 1),
            (0.2, "accepted", 2, 1, 0),
            (0.4, "rejected", 3, 0, 0),
            (1.0, "completed", 1, 5, 5),
            (1.0, "accepted", 4, 5, 0),
            (1.2, "completed", 2, 1, 1),
            (2.0, "completed", 4, 5, 6),
        ]
        self.assertEqual(len(result["events"]), len(expected))
        for event, (time, kind, job_id, allocation, idle) in zip(result["events"], expected):
            self.assertAlmostEqual(event["time"], time)
            self.assertEqual((event["event"], event["job_id"],
                              event["allocated_servers"], event["idle_servers"]),
                             (kind, job_id, allocation, idle))
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (3, 1, 3))
        self.check_conservation(result, 6)

    def test_all_simultaneous_completions_precede_arrival(self):
        result = simulate([(0, 3.4), (0, 1), (1, 3.4)], servers=6)
        at_one = [(e["event"], e["job_id"], e["idle_servers"])
                  for e in result["events"] if e["time"] == 1]
        self.assertEqual(at_one, [("completed", 1, 5), ("completed", 2, 6), ("accepted", 3, 1)])
        self.assertEqual(result["rejected"], 0)
        self.check_conservation(result, 6)

    def test_simultaneous_arrivals_follow_input_order(self):
        result = simulate([(0, 3.4), (0, 1), (0, 2)], servers=6)
        arrivals = [e for e in result["events"] if e["event"] != "completed"]
        self.assertEqual([(e["event"], e["job_id"]) for e in arrivals],
                         [("accepted", 1), ("accepted", 2), ("rejected", 3)])
        self.check_conservation(result, 6)

    def test_one_server_rejection_and_release(self):
        result = simulate([(0, 2), (1, 1), (2, 1)], servers=1)
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (2, 1, 2))
        self.assertEqual(result["events"][-1]["time"], 3)
        self.check_conservation(result, 1)

    def test_empty_input(self):
        result = simulate([], servers=6)
        self.assertEqual(result["events"], [])
        self.assertEqual(result["arrivals"], 0)
        self.check_conservation(result, 6)

    def test_rejects_invalid_inputs(self):
        for servers in [0, -1, 1.5, True]:
            with self.subTest(servers=servers), self.assertRaises(ValueError):
                simulate([], servers=servers)
        for arrivals in [[(-1, 1)], [(1, 1), (0, 1)], [(0, -1)],
                         [(float("inf"), 1)], [(0, float("nan"))]]:
            with self.subTest(arrivals=arrivals), self.assertRaises(ValueError):
                simulate(arrivals)


if __name__ == "__main__":
    unittest.main()
