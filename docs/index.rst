.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   Guides <guides/index>
   Development Guide <dev_guide/index>
   API Docs <apidocs/index>

Aardvark
=========================

.. warning::
   Aardvark is still under development, and thus volatile. It is not guaranteed
   that data saved with this version will be loadable in future versions.

Aardvark provides serialisation support and experiment data management for
research use-cases. Through the associated ``asdf-qiskit`` library, important
Qiskit classes are saved into :mod:`asdf` files. This allows developers and
researchers to save experimental data in a format that is both human readable
and well supported. The most important feature of Aardvark is the handling of
artifacts (or aard-ifacts), which are files separate from the serialised data
that are still associated with the experiment.

`ASDF <https://www.asdf-format.org/en/latest/>`_ is a derivative of YAML that
supports multidimensional arrays and memory-mapped data support for simpler
data management. With Aardvark you can save Qiskit classes and experimental
results with ASDF without needing to worry about backwards compatibility [1]_,
like with pickle. ASDF and YAML was chosen given their human readability and
support for Python and NumPy datatypes.

Aardvark actually consists of two libraries: ``asdf_qiskit`` which is an
`ASDF <https://www.asdf-format.org/en/latest/>`_ plugin to support Qiskit
class serialisation, and ``aardvark`` which provides the :class:`~aardvark.Experiment`
interface and artifact support.

This documentation is divided into a few sections, depending on your
understanding of Python, ASDF, and serialisation.

.. grid:: 2

   .. grid-item-card:: Getting Started
      :link: guides/index
      :link-type: doc

      Getting started with Aardvark.

   .. grid-item-card:: Supported Types
      :link: guides/supported_types
      :link-type: doc

      Breakdown of which classes in Qiskit and Python are serialised by
      ``asdf-qiskit``.

.. grid:: 2

   .. grid-item-card:: Development Guide
      :link: dev_guide/index
      :link-type: doc

      Information on how ``aardvark`` and ``asdf_qiskit`` are architected and
      how to contribute to the code-base.


   .. grid-item-card:: API Docs
      :link: apidocs/index
      :link-type: doc

      Detailed information about the implementation of ``aardvark`` and
      ``asdf_qiskit``.



.. [1] At least, this is the goal with Aardvark. Though data may not be
    serialisable into the same classes in Qiskit if, for example, the class is
    deprecated and removed. But the intention is to (i) support existing
    classes in the latest supported versions of Qiskit, (ii) have clearly
    defined schemas for how quantum computing data is represented in ASDF/YAML,
    and (iii) common sense ways to load saved data in new versions of Qiskit.

Index
=====

* :ref:`genindex`
* :ref:`modindex`
