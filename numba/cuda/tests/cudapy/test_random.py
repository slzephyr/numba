from __future__ import print_function, division, absolute_import

import math

import numpy as np

from numba import cuda, config, float32
from numba.cuda.testing import unittest
import numba.cuda.random

# Distributions
UNIFORM = 1
NORMAL = 2


@cuda.jit
def rng_kernel_float32(states, out, count, distribution):
    thread_id = cuda.grid(1)

    for i in range(count):
        if distribution == UNIFORM:
            out[thread_id * count + i] = cuda.random.xoroshiro128p_uniform_float32(states, thread_id)
        elif distribution == NORMAL:
            out[thread_id * count + i] = cuda.random.xoroshiro128p_normal_float32(states, thread_id)


@cuda.jit
def rng_kernel_float64(states, out, count, distribution):
    thread_id = cuda.grid(1)
    nthreads = cuda.gridsize(1)

    for i in range(count):
        if distribution == UNIFORM:
            out[thread_id * count + i] = cuda.random.xoroshiro128p_uniform_float64(states, thread_id)
        elif distribution == NORMAL:
            out[thread_id * count + i] = cuda.random.xoroshiro128p_normal_float64(states, thread_id)


class TestCudaRandomXoroshiro128p(unittest.TestCase):
    def test_create(self):
        states = cuda.random.create_xoroshiro128p_states(10, seed=1)
        s = states.copy_to_host()
        self.assertEqual(len(np.unique(s)), 10)

    def test_create_subsequence_start(self):
        states = cuda.random.create_xoroshiro128p_states(10, seed=1)
        s1 = states.copy_to_host()

        states = cuda.random.create_xoroshiro128p_states(10, seed=1,
            subsequence_start=3)
        s2 = states.copy_to_host()

        # Starting seeds should match up with offset of 3
        np.testing.assert_array_equal(s1[3:], s2[:-3])

    def test_create_stream(self):
        stream = cuda.stream()
        states = cuda.random.create_xoroshiro128p_states(10, seed=1, stream=stream)
        s = states.copy_to_host()
        self.assertEqual(len(np.unique(s)), 10)

    def check_uniform(self, kernel_func, dtype):
        states = cuda.random.create_xoroshiro128p_states(64*10, seed=1)
        out = np.zeros(10 * 64 * 128, dtype=np.float32)

        kernel_func[10, 64](states, out, 128, UNIFORM)
        self.assertAlmostEqual(out.min(), 0.0, places=4)
        self.assertAlmostEqual(out.max(), 1.0, places=4)
        self.assertAlmostEqual(out.mean(), 0.5, places=3)
        self.assertAlmostEqual(out.std(), 1.0/(2*math.sqrt(3)), places=3)

    def test_uniform_float32(self):
        self.check_uniform(rng_kernel_float32, np.float32)

    def test_uniform_float64(self):
        self.check_uniform(rng_kernel_float64, np.float64)

    def check_normal(self, kernel_func, dtype):
        states = cuda.random.create_xoroshiro128p_states(64 * 10, seed=1)
        out = np.zeros(10 * 64 * 128, dtype=dtype)

        kernel_func[10, 64](states, out, 128, NORMAL)

        self.assertAlmostEqual(out.mean(), 0.0, places=2)
        self.assertAlmostEqual(out.std(), 1.0, places=2)

    def test_normal_float32(self):
        self.check_normal(rng_kernel_float32, np.float32)

    def test_normal_float32(self):
        self.check_normal(rng_kernel_float64, np.float64)

if __name__ == '__main__':
    unittest.main()
