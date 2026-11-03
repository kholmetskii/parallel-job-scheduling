import unittest

from simulation import EXAMPLE_ARRIVALS, Job, ServerPool, Simulator


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
        result = Simulator(servers=6).run(EXAMPLE_ARRIVALS)
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
        result = Simulator(servers=6).run([(0, 3.4), (0, 1), (1, 3.4)])
        at_one = [(e["event"], e["job_id"], e["idle_servers"])
                  for e in result["events"] if e["time"] == 1]
        self.assertEqual(at_one, [("completed", 1, 5), ("completed", 2, 6), ("accepted", 3, 1)])
        self.assertEqual(result["rejected"], 0)
        self.check_conservation(result, 6)

    def test_simultaneous_arrivals_follow_input_order(self):
        result = Simulator(servers=6).run([(0, 3.4), (0, 1), (0, 2)])
        arrivals = [e for e in result["events"] if e["event"] != "completed"]
        self.assertEqual([(e["event"], e["job_id"]) for e in arrivals],
                         [("accepted", 1), ("accepted", 2), ("rejected", 3)])
        self.check_conservation(result, 6)

    def test_one_server_rejection_and_release(self):
        result = Simulator(servers=1).run([(0, 2), (1, 1), (2, 1)])
        self.assertEqual((result["accepted"], result["rejected"], result["completed"]), (2, 1, 2))
        self.assertEqual(result["events"][-1]["time"], 3)
        self.check_conservation(result, 1)

    def test_empty_input(self):
        result = Simulator(servers=6).run([])
        self.assertEqual(result["events"], [])
        self.assertEqual(result["arrivals"], 0)
        self.check_conservation(result, 6)

    def test_rejects_invalid_inputs(self):
        for servers in [0, -1, 1.5, True]:
            with self.subTest(servers=servers), self.assertRaises(ValueError):
                Simulator(servers=servers).run([])
        for arrivals in [[(-1, 1)], [(1, 1), (0, 1)], [(0, -1)],
                         [(float("inf"), 1)], [(0, float("nan"))]]:
            with self.subTest(arrivals=arrivals), self.assertRaises(ValueError):
                Simulator().run(arrivals)


class ObjectModelTests(unittest.TestCase):
    def test_job_stores_timing_and_cannot_be_reallocated(self):
        job = Job(job_id=7, arrival_time=0.2, size=3.4)
        self.assertEqual(job.allocated_servers, 0)
        self.assertIsNone(job.completion_time)
        self.assertIsNone(job.start(5))
        self.assertEqual(job.allocated_servers, 5)
        self.assertAlmostEqual(job.completion_time, 1.2)
        with self.assertRaises(RuntimeError):
            job.start(1)
        self.assertEqual(job.allocated_servers, 5)
        self.assertAlmostEqual(job.completion_time, 1.2)

    def test_pool_prevents_overallocation_and_overrelease(self):
        pool = ServerPool(6)
        pool.allocate(5)
        self.assertEqual((pool.idle_servers, pool.occupied_servers), (1, 5))
        for operation, count in [("allocate", 2), ("release", 6),
                                 ("allocate", 0), ("release", 0)]:
            with self.subTest(operation=operation, count=count), self.assertRaises(ValueError):
                getattr(pool, operation)(count)
            self.assertEqual((pool.idle_servers, pool.occupied_servers), (1, 5))
        pool.release(5)
        self.assertEqual((pool.idle_servers, pool.occupied_servers), (6, 0))

    def test_reusing_simulator_starts_fresh_and_preserves_previous_result(self):
        simulator = Simulator(servers=6)
        first = simulator.run(EXAMPLE_ARRIVALS)
        first_events = [event.copy() for event in first["events"]]
        second = simulator.run([(0, 3.4)])
        self.assertEqual((second["arrivals"], second["accepted"],
                          second["rejected"], second["completed"]), (1, 1, 0, 1))
        self.assertEqual(second["events"][0]["job_id"], 1)
        self.assertEqual(second["final_idle_servers"], 6)
        self.assertIsNot(first["events"], second["events"])
        self.assertEqual(first["events"], first_events)
        self.assertEqual((first["arrivals"], first["accepted"], first["completed"]), (4, 3, 3))

    def test_simulator_instances_have_independent_state(self):
        first = Simulator(servers=6)
        second = Simulator(servers=1)
        first.run(EXAMPLE_ARRIVALS)
        second.run([(0, 4), (1, 1)])
        self.assertEqual((first.current_time, first.accepted, first.rejected), (2, 3, 1))
        self.assertEqual((second.current_time, second.accepted, second.rejected), (4, 1, 1))
        self.assertEqual(first.pool.idle_servers, 6)
        self.assertEqual(second.pool.idle_servers, 1)


if __name__ == "__main__":
    unittest.main()
