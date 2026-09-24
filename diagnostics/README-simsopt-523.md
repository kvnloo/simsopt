# SIMSOPT #523: native contract diagnostic

AI-assisted diagnostic preparation. Upstream code inspected at
`9e027eac38028d57aa23777be52a781aa860e347` (2026-09-14).

## Why this is not a production patch

The upstream tests already establish that a regular-grid interpolant with
`out_of_bounds_ok=True` leaves the destination unchanged for missing cells.
`Testing.test_out_of_bounds` and `Testing.test_skip` in
`tests/field/test_interpolant.py` explicitly protect that behavior.

A cached field can therefore accidentally return the previous evaluation when
it passes a reused buffer to this low-level API. The field-level test observes
the same outside point after two different valid points. It uses `BoozerAnalytic`
instead of VMEC or equilibrium files and copies results to avoid observation
aliasing. It allows a consistent RuntimeError or a history-independent result;
it does not choose an extrapolation/sentinel policy.

## Execution and interpretation

Run `python diagnostics/simsopt_523.py` in a source-built SIMSOPT environment
(or `python simsopt_523.py` in this downloaded packet).

There are five low-level controls and one field-history regression. None are
marked expected failure or continue-on-error. A failing history regression,
with the controls passing, is useful baseline evidence, not a fixed bug.
No native result was obtained in the local ChatGPT container: importing
`simsoptpp` failed, and package installation could not reach its package index.
Only Python syntax compilation was completed locally. The accompanying
`local-attempt.log` records exit code 2, meaning no native tests ran.

## Fork CI isolation

The disposable branch `probe/simsopt-523-native-20260924` is a CI diagnostic,
not an upstream PR branch. On this branch only, the inherited workflow directory
is replaced by a single small CPU probe to avoid automatically launching the
upstream integration/publishing workflows. All production sources remain at the
base commit. The fork's default branch and upstream are unchanged.

The workflow builds the checked-out package, records the commit, submodule
revisions, resolved packages and native logs, and uses read-only token
permissions. It has no schedule, deployment, secret access, or upstream write.

## Sources

- https://github.com/hiddenSymmetries/simsopt/issues/523
- https://github.com/hiddenSymmetries/simsopt/blob/9e027eac38028d57aa23777be52a781aa860e347/tests/field/test_interpolant.py
- https://github.com/hiddenSymmetries/simsopt/blob/9e027eac38028d57aa23777be52a781aa860e347/tests/field/test_boozermagneticfields.py
- https://github.com/ColumbiaStellaratorTheory/firm3d/pull/50

Contribution-guide check: `docs/source/contributing.rst` at the inspected commit
contains no explicit AI restriction. This is not a claim of special permission;
any upstream proposal should disclose AI assistance and its actual test scope.
