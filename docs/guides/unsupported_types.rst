.. _my_unsupported_types:

Unsupported Types
#################

Some types in Python, Qiskit, and other python libraries are not supported by
Exprés or ASDF. This document lists some important ones and the reasons we have
not implemented support. In some cases, workarounds are given for how best to
store these types.


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
