.. _my_unsupported_types:

Unsupported Types
#################

Some types in Python, Qiskit, and other quantum computing libraries are not
supported by ``asdf-qiskit``. This document lists some important ones, reasons
for not supporting them in ``asdf-qiskit``, and in some cases, recommended ways
for storing them in supported data structures.


Python
******

:mod:`uncertainties`
====================

The :mod:`uncertainties` module provides uncertainties support for numerical
value, automatically propagating uncertainties through common mathematical
operations including with :mod:`numpy`. At face-value, this is not something
difficult to serialise. However, internally, ``uncertainties`` tracks the
original variables that impact the resulting uncertainty. Serialising these
would result in a complicated ``ASDF`` file that is not human readable. There
are two recommended ways around this:

1. Compute the final values with uncertainties and then save the nominal values
   and standard deviations as two separate entries. For example, as ``"x"`` and
   ``"x_stderr"`` keys in the tree. This destroys correlations between
   variables, and is thus most appropriate for the final output of a simulation
   or experiment.
2. Save the original values so you can recompute the outputs if necessary. For
   example, the output of a curve fit gives estimates of parameter values and
   the covariance matrix. Save the fits as ``"x"``, their estimated standard
   errors as ``"x_stderr"``, and the covariance matrix as ``"x_covar"``.
   :mod:`uncertainties` supports creating :class:`~uncertainties.UFloat`
   instances from covariance matrices: see
   :func:`~uncertainties.correlated_values`.

Qiskit
******

Backends
========

Backends in Qiskit and ``qiskit-ibm-runtime`` are complicated, and much of their
definitions in Python manage API calls to IBM servers. Additionally, any
implementation would be specific to IBM hardware, ignoring alternative
providers. In the end, researchers and developers typically want to store two
types of information relating to backends:

1. References to the exact backend used for an experiment.
2. Properties of the backend.

For the former, saving the backend name should be sufficient. This also allows
for easy reloading of the same backend correctly, with something akin to
``service.backend(tree["backend"])``. For saving properties, it is recommended
that users store properties as dictionaries of property values.
