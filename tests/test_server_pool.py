import unittest

from scheduling.job import Job
from scheduling.server_pool import ServerPool
from tests.fixtures import SPEEDUPS


class ServerPoolTests(unittest.TestCase):
    def test_accepts_single_linear_and_rounded_speedups(self):
        for speedups in ((1,), (1, 2, 3, 4, 5), SPEEDUPS, (1, 1.1, 1.2, 1.3)):
            with self.subTest(speedups=speedups):
                ServerPool(1, speedups)

    def test_copies_speedups_from_caller(self):
        speedups = [1, 1.8, 2.5]
        pool = ServerPool(3, speedups)
        speedups[1] = 10
        self.assertEqual(pool.speedups, (1, 1.8, 2.5))

    def test_starting_and_completing_jobs_keep_capacity_and_schedule_together(self):
        pool = ServerPool(6, speedups=SPEEDUPS)
        first = Job(id=20, size=3.4, arrival_time=0)
        second = Job(id=3, size=1, arrival_time=0)
        self.assertEqual(pool.start_job(first, 5), 1)
        self.assertEqual((pool.idle_servers, pool.occupied_servers), (1, 5))
        self.assertEqual(pool.start_job(second, 1), 1)
        self.assertEqual(pool.idle_servers, 0)
        self.assertEqual(pool.next_completion_time(), 1)
        self.assertEqual(pool.complete_next(), (1, 1, second))
        self.assertEqual(pool.idle_servers, 1)
        self.assertEqual(pool.complete_next(), (1, 5, first))
        self.assertEqual((pool.idle_servers, pool.occupied_servers), (6, 0))
        self.assertIsNone(pool.next_completion_time())

    def test_blocking_and_invalid_allocations_leave_capacity_and_schedule_unchanged(self):
        pool = ServerPool(1, speedups=SPEEDUPS)
        first = Job(id=1, size=2, arrival_time=0)
        blocked = Job(id=2, size=1, arrival_time=1)
        with self.assertRaises(ValueError):
            pool.start_job(first, 0)
        self.assertIsNone(pool.next_completion_time())
        pool.start_job(first, 1)
        self.assertIsNone(pool.start_job(blocked, 0))
        for allocation in (-1, 1, True, 1.5):
            with self.subTest(allocation=allocation), self.assertRaises(ValueError):
                pool.start_job(blocked, allocation)
            self.assertEqual(pool.idle_servers, 0)
            self.assertEqual(pool.next_completion_time(), 2)
        self.assertEqual(pool.complete_next(), (2, 1, first))
        with self.assertRaises(IndexError):
            pool.complete_next()
        self.assertEqual(pool.idle_servers, 1)

    def test_nonfinite_completion_does_not_reserve_or_schedule_work(self):
        pool = ServerPool(1, speedups=SPEEDUPS)
        job = Job(id=1, size=1e308, arrival_time=1e308)
        with self.assertRaisesRegex(ValueError, "Completion time"):
            pool.start_job(job, 1)
        self.assertEqual(pool.idle_servers, 1)
        self.assertIsNone(pool.next_completion_time())

    def test_custom_speedups_define_execution_time_and_maximum_allocation(self):
        pool = ServerPool(5, speedups=(1, 1.5, 2))
        job = Job(id=1, size=6, arrival_time=2)
        with self.assertRaises(ValueError):
            pool.start_job(job, 4)
        self.assertEqual(pool.idle_servers, 5)
        self.assertEqual(pool.start_job(job, 3), 5)
        self.assertEqual(pool.complete_next(), (5, 3, job))
        self.assertEqual(pool.idle_servers, 5)


if __name__ == "__main__":
    unittest.main()
