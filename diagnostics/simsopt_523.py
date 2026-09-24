"""Fork-only native diagnostic for hiddenSymmetries/simsopt#523.

AI-assisted diagnostic. Preserve the low-level output-buffer contract and test
field-history independence without choosing an extrapolation policy. No VMEC,
MPI, GPU, or external equilibrium files are needed for this analytic probe.
"""
import importlib.metadata
import platform
import sys
import unittest

import numpy as np

try:
    import simsoptpp as sopp
    from simsopt.field.boozermagneticfield import BoozerAnalytic, InterpolatedBoozerField
except ImportError as exc:
    print(f"NATIVE TESTS NOT RUN: SIMSOPT import failed: {exc}", file=sys.stderr)
    raise SystemExit(2) from exc


def linear(x, y, z):
    return np.ascontiguousarray(
        np.asarray(x) + 2.0 * np.asarray(y) + 3.0 * np.asarray(z)
    ).ravel()


def interpolant(allowed=True, skip=None):
    args = (sopp.UniformInterpolationRule(1), (0., 1., 4),
            (0., 1., 4), (0., 1., 4), 1, allowed)
    obj = sopp.RegularGridInterpolant3D(*args) if skip is None else sopp.RegularGridInterpolant3D(*args, skip)
    obj.interpolate_batch(linear)
    return obj


class TestLowLevelContract(unittest.TestCase):
    def test_prefilled_sentinel_is_preserved(self):
        out = np.full((1, 1), -1.0)
        interpolant().evaluate_batch(np.array([[1.01, .25, .25]]), out)
        np.testing.assert_array_equal(out, [[-1.0]])

    def test_reused_buffer_is_deliberately_left_unchanged(self):
        obj = interpolant()
        out = np.full((1, 1), -1.0)
        obj.evaluate_batch(np.array([[.25, .25, .25]]), out)
        np.testing.assert_allclose(out, [[1.5]], rtol=0., atol=1e-12)
        before = out.copy()
        obj.evaluate_batch(np.array([[1.01, .25, .25]]), out)
        np.testing.assert_array_equal(out, before)

    def test_mixed_batch_preserves_only_outside_row(self):
        xyz = np.array([[.25, .25, .25], [1.01, .25, .25], [.75, .25, .25]])
        out = np.full((3, 1), -7.0)
        interpolant().evaluate_batch(xyz, out)
        np.testing.assert_allclose(out, [[1.5], [-7.0], [2.0]], rtol=0., atol=1e-12)

    def test_skipped_in_domain_cell_preserves_sentinel(self):
        def skip(x, y, z):
            return np.asarray(x) >= .5

        xyz = np.array([[.125, .25, .25], [.875, .25, .25]])
        out = np.full((2, 1), -9.0)
        interpolant(skip=skip).evaluate_batch(xyz, out)
        np.testing.assert_allclose(out, [[1.375], [-9.0]], rtol=0., atol=1e-12)

    def test_strict_mode_raises(self):
        out = np.full((1, 1), -1.0)
        with self.assertRaises(RuntimeError):
            interpolant(allowed=False).evaluate_batch(np.array([[1.01, .25, .25]]), out)


def make_field():
    analytic = BoozerAnalytic(.1, 1.0, 0, 1.0, 1.0, .4)
    field = InterpolatedBoozerField(
        analytic, 3, (.1, 1.0, 4), (0., np.pi, 4), (0., 2*np.pi, 4),
        extrapolate=True, nfp=1, stellsym=True,
    )
    # Keep the Python-defined field alive as well as its C++ base object.
    # The existing binding already supplies the virtual-method trampoline.
    return analytic, field


def outside_outcome(field):
    field.set_points(np.array([[1.01, .4, .2]]))
    try:
        # Copy observations so they cannot alias the mutable cache.
        return ("value", np.array(field.modB(), copy=True))
    except RuntimeError as exc:
        return ("error", type(exc).__name__, str(exc))


class TestCachedFieldHistory(unittest.TestCase):
    def test_same_outside_point_is_independent_of_previous_point(self):
        analytic, field = make_field()
        # Validate Python virtual dispatch before attempting the regression.
        analytic.set_points(np.array([[.25, .4, .2]]))
        np.testing.assert_allclose(
            analytic.modB(), [[1.0 + .1 * np.sqrt(.5) * np.cos(.4)]],
            rtol=0., atol=1e-12,
        )
        print("Analytic source sanity check passed", flush=True)
        snapshots = []
        outcomes = []
        for s in (.25, .75):
            field.set_points(np.array([[s, .4, .2]]))
            snapshots.append(np.array(field.modB(), copy=True))
            outcomes.append(outside_outcome(field))
        self.assertTrue(all(np.isfinite(x).all() for x in snapshots))
        self.assertFalse(np.allclose(snapshots[0], snapshots[1]))
        print("Primed in-domain values:", [x.tolist() for x in snapshots], flush=True)
        print("Repeated outside-point outcomes:", [
            (x[0], x[1].tolist()) if x[0] == "value" else x for x in outcomes
        ], flush=True)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        if outcomes[0][0] == "error":
            self.assertEqual(outcomes[0][1], outcomes[1][1])
        else:
            np.testing.assert_allclose(
                outcomes[0][1], outcomes[1][1], rtol=0., atol=1e-12, equal_nan=True,
                err_msg="The same outside point depends on a previous in-domain point",
            )


if __name__ == "__main__":
    print("Platform:", platform.platform(), flush=True)
    print("Python:", sys.version, flush=True)
    print("SIMSOPT:", importlib.metadata.version("simsopt"), flush=True)
    print("Native extension:", sopp.__file__, flush=True)
    unittest.main(verbosity=2)
