# Diagnostic corrections, 2026-09-24

The run at 8b140566 failed before any native tests ran: literal backslash-n
characters introduced by the assistant caused a SyntaxError. This is not an
upstream SIMSOPT result.

The proposed BoozerMagneticFieldPythonTrampoline constructor was not verified
and is not exposed by the inspected bindings. The bindings already register
PyBoozerMagneticFieldTrampoline for BoozerMagneticField. Remove the unsupported
call rather than treating it as a repair.

The corrected analytic probe retains the Python source field alongside the
interpolated field. A shared C++ base pointer need not keep the Python subclass
alive; losing the latter is a candidate explanation for the original
_modB_impl error. This hypothesis still requires native execution.

The source-field sanity check runs before the field-history experiment.
The five low-level contract tests remain. Python syntax compilation passed
locally; the six native tests were not run in the local container because
simsoptpp is unavailable. The workflow now checks syntax before building.
No production code changed and no upstream comment or PR was created.

Sources:
- https://github.com/hiddenSymmetries/simsopt/blob/9e027eac38028d57aa23777be52a781aa860e347/src/simsoptpp/python_boozermagneticfield.cpp
- https://github.com/hiddenSymmetries/simsopt/blob/9e027eac38028d57aa23777be52a781aa860e347/src/simsoptpp/pyboozermagneticfield.h
- https://pybind11.readthedocs.io/en/stable/advanced/classes.html#avoiding-inheritance-slicing-and-std-weak-ptr-surprises
