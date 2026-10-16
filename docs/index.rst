.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   Guides <guides/index>
   Development Guide <dev_guide/index>
   API Docs <apidocs/index>

Exprés
=========================

.. warning::
   Exprés is still under development, and thus volatile. It is not guaranteed
   that data saved with this version will be loadable in future versions.

Exprés provides serialisation support and experiment data management for
research use-cases. `ASDF <https://www.asdf-format.org/en/latest/>` provides
support for saving important Python classes and datastructures into mostly
human-readable YAML. This allows developers and researchers to save experimental
data in a format that is both easy to understand and well supported by analysis
tools and experimentation software. The most important feature of Exprés is the
handling of artifacts, which are files separate from the serialised data that
are still associated with the experiment.

`ASDF <https://www.asdf-format.org/en/latest/>`_ is a superset of YAML that
supports multidimensional arrays and memory-mapped data support for simpler data
management. With Exprés you can save experimental results with ASDF without
needing to worry about backwards compatibility issues [1]_, like with pickle.
ASDF and YAML were chosen given their human readability and support for Python
and NumPy datatypes.

This documentation is divided into a few sections, depending on your
understanding of Python, ASDF, and serialisation.

.. grid:: 2

   .. grid-item-card:: Getting Started
      :link: guides/index
      :link-type: doc

      Getting started with Exprés.

   .. grid-item-card:: Supported Types
      :link: guides/supported_types
      :link-type: doc

      Breakdown of which classes in are serialised by Exprés.

.. grid:: 2

   .. grid-item-card:: Development Guide
      :link: dev_guide/index
      :link-type: doc

      Information on how Exprés is architected and how to contribute to the
      code-base.


   .. grid-item-card:: API Docs
      :link: apidocs/index
      :link-type: doc

      Detailed information about the implementation of Exprés.



.. [1] At least, this is the goal with Exprés. The intention is to (i) support
    existing data and experiments in the latest supported versions of ASDF and
    Python, (ii) have clearly defined schemas for how experiments are
    represented in ASDF/YAML, and (iii) common sense ways to load saved data in
    new versions of Exprés.

Index
=====

* :ref:`genindex`
* :ref:`modindex`
