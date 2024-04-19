.. _guides_installation:

Installation
############


As ``aardvark`` and ``asdf_qiskit`` are still under active development, they
are not yet on PyPI. Therefore, it is necessary to install from source. You can
do that with pip as follows:

.. code-block:: bash

   git clone <git repo url>
   pip install aardvark/asdf-qiskit
   pip install aardvark/aardvark

Running Tests
*************

You can also test if everything works by running tests:

.. code-block:: bash

   cd aardvark
   pip install '.[dev]'
   cd ../asdf-qiskit
   pip install '.[dev]'
   cd ..
   pytest

Note that in practice Tox is used to run tests. For information about how to run
all tests with Tox, look at the ``tox.ini`` files in the code-base.

Compatibility Tests
*******************

ASDF Qiskit has additional tests to verify Python and Qiskit version
compatibility. These are run with Tox and are defined in
``asdf_qiskit/compatibility_tests``. They have two steps: (i) tests are run and
serialisable objects are captured, serialised, and saved to files; and then (ii)
the tests are run, loading the saved data as a secondary object and comparing it
to the generated object in the current Python environment. These are defined in
the ``tox.ini`` file for ASDF Qiskit, in the ``save-*`` and ``load-*``
environments.
