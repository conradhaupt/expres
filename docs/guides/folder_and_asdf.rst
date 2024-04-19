.. _guides_folder_and_asdf:

Experiment Folders and ASDF Structure
#####################################

Experiments are saved into ASDF files, which store all non-artifact data from an
experiment instance. These are saved into a folder alongside all artifacts. An
ASDF file is a YAML file with special encoding for nearly all Python data types
and Qiskit classes [1]_.

Example Experiment
******************

To illustrate how data and artifacts are saved, as well as the structure of the
resulting folder and ASDF file, we will create a dummy experiment called
``Simulation``. Consider we have some script called ``simulation.py`` which has
the following contents:

.. code-block:: python

    # Common imports
    import matplotlib.pyplot as plt
    import numpy as np
    import numpy.typing as npt

    # We import the important class and functions from Aardvark.
    from aardvark import Experiment, artifact, dataclass, field

    # All experiments must be dataclasses.
    @dataclass
    class Simulation(Experiment):
    
        # Input arguments
        t_steps: list[float]
        params: list[float]

        # Simulation results.
        energies: npt.NDArray | None = field(default=None)
        metrics: npt.NDArray | None = artifact(
            default=None,
            format="npz",
            source="metrics_over_time.npz",
        )

    # Create an instance of our experiment class.
    exp = Simulation(
        t_steps=list(np.linspace(0, 1, 10).astype(float)),
        params=[0.5, 0.5],
    )

    
    # We Run our simulation and get some data. Here we use some dummy random data.
    exp.energies = np.random.normal(size=(100,))
    exp.metrics = np.random.uniform(0, 1, (len(exp.t_steps),))

    # Create a figure and save it to the experiment.
    fig, ax = plt.subplots(1, 1)
    ax.plot(exp.metrics)
    ax.set_xlabel("Control")
    ax.set_ylabel("Metric")

    # Save the figure as a PDF to the experiment, which is saved as an artifact.
    exp.savefig(fig, "fig1.pdf", bbox_inches="tight")

    # Save the experiment and the artifacts to a folder.
    exp.save()


Let's breakdown what is happening in this script.

.. code-block:: python

    # Common imports
    import matplotlib.pyplot as plt
    import numpy as np
    import numpy.typing as npt

    # We import the important class and functions from Aardvark.
    from aardvark import Experiment, artifact, dataclass, field

Here we import the necessary modules for our simulation. All the important
functionality from Aardvark is available as root-module imports. This includes
:class:`Experiment`, :func:`artifact`, :func:`dataclass`, and :func:`field`. We
use these to define our experiment class, which has to be a dataclass.

.. code-block:: python

    @dataclass
    class Simulation(Experiment):
    
        # Input arguments
        t_steps: list[float]
        params: list[float]

        # Simulation results.
        energies: npt.NDArray | None = field(default=None)
        metrics: npt.NDArray | None = artifact(
            default=None,
            format="npz",
            source="metrics_over_time.npz",
        )

Our experiment subclasses :class:`Experiment` so we have save and load
functionality, and support for artifacts. The :func:`dataclass` decorator allows
us to define attributes without defining an ``__init__`` method. In this
scenario, ``t_steps`` and ``params`` are lists of floats that are required,
i.e., they do not have a default value. However, ``energies`` will store values
we compute during our simulation and so we don't have them when we create our
experiment instance. One way of handling this is to set the default to None with
:func:`field`.

The same is true for ``metrics``, except we want to store its values outside of
the saved ASDF file. In this context, ``metrics`` is a bound artifact: an
artifact that is bound to an experiment attribute. We declare a bound artifact
with :func:`artifact`, which behaves similarly to :func:`field`. We can define a
default value, but we need to state the format. In this scenario, it is a Numpy
``npz`` file. We can also override the default filename for this artifact by
setting ``source``. By default, the numpy artifact handler will use the
attribute name as the filename, with the ``.npz`` suffix.

.. code-block:: python

    # Create an instance of our experiment class.
    exp = Simulation(
        t_steps=list(np.linspace(0, 1, 10).astype(float)),
        params=[0.5, 0.5],
    )

    
    # We Run our simulation and get some data. Here we use some dummy random data.
    exp.energies = np.random.normal(size=(100,))
    exp.metrics = np.random.uniform(0, 1, (len(exp.t_steps),))

Here we create an instance of our experiment, assigning values to attributes
``t_steps`` and ``params``. We can assign the values of any attributes later,
such as after running our simulations. Note that ``exp.energies`` and
``exp.metrics`` are assigned in the same way even though one is a bound artifact
and one is not.

.. code-block:: python

    # Create a figure and save it to the experiment.
    fig, ax = plt.subplots(1, 1)
    ax.plot(exp.metrics)
    ax.set_xlabel("Control")
    ax.set_ylabel("Metric")

    # Save the figure as a PDF to the experiment, which is saved as an artifact.
    exp.savefig(fig, "fig1.pdf", bbox_inches="tight")

    # Save the experiment and the artifacts to a folder.
    exp.save()

We can also create a figure and save it as an artifact. Instead of calling
:func:`~matplotlib.pyplot.savefig`, we call :meth:`Experiment.savefig`. This
effectively does the same, but instead saves to a file associated with our
experiment. We can also save figures and open artifacts before we've saved our
experiment. Their files live in a temporary folder until we call
:meth:`Experiment.save`, at which point they are copied to the final experiment
folder.

Folder Structure
****************

Now that we've saved our experiment, we want to investigate the folder into
which it was saved. In our current working directory we will find the following
new directory tree.::

    ├── simulation.py
    └── Simulation_20260114_0012_3b620d7d
        ├── metrics_over_time.npz
        ├── fig1.pdf
        └── Simulation_20260114_0012_3b620d7d.asdf

The first file is our script. The folder represents an experiment we created and
saved. We can tell the Experiment class and creation date from the folder name:
the class is called ``Simulation`` and it was created on 14 November, 2026 at 12
minutes past midnight UTC time. Note that all dates and times created by
Aardvark are in UTC time. The last part of the names, ``3b620d7d``, is the first
eight hexadecimal characters of the experiment's :class:`UUID`. Each experiment
instance has a unique identifier for easier tracking.

Inside the folder there are three files: the Numpy npz file for ``exp.metrics``,
the figure we saved, and the ASDF file storing the rest of our experiment data.
The pdf and npz files are artifacts and can be shared freely and have no links
back to the ASDF file. The ASDF file keeps track of which artifacts were
created, while storing all other data in its ASDF tree, which is like a
dictionary.

ASDF Files
**********

ASDF files are just YAML and thus the bulk of their contents should be familiar
to those who have used the file-format for other uses, such as configuration
files. The major differences to YAML are in the header, certain properties that
are always present, and the binary blocks at the end of the file. The ASDF file
we saved is shown below, without some verbose sections that aren't relevant to
this guide.

.. code-block:: yaml

    #ASDF 1.0.0
    #ASDF_STANDARD 1.6.0
    %YAML 1.1
    %TAG ! tag:stsci.edu:asdf/
    %TAG !qiskit! asdf://qiskit.org/asdf/tags/
    %TAG !aardvark! asdf://aardvark.org/asdf/tags/
    --- !core/asdf-1.1.0
    uuid: !qiskit!core/uuid-0.0.0 3b620d7d7d024a01b2b62f25988b3461
    date_created: 2026-11-14 00:12:12.927647+00:00
    description: null
    asdf_library: !core/software-1.0.0 {author: The ASDF Developers, homepage: 'http://github.com/asdf-format/asdf',
      name: asdf, version: 5.0.0}
    history:
    extensions:
    - !core/extension_metadata-1.0.0
      ...
    artifacts: !aardvark!core/artifacts-0.0.0
        fig1.pdf: {source: fig1.pdf}
    energies: !core/ndarray-1.1.0
        byteorder: little
        datatype: float64
        shape: [100]
        source: 0
    metrics: !aardvark!core/artifact-0.0.0 {format: npz, source: metrics_over_time.npz}
    params: [0.5, 0.5]
    t_steps: [0.0, 0.1111111111111111, 0.2222222222222222, 0.3333333333333333, 0.4444444444444444,
      0.5555555555555556, 0.6666666666666666, 0.7777777777777777, 0.8888888888888888,
      1.0]
    ...
    <binary data>#ASDF BLOCK INDEX
    %YAML 1.1
    ---
    - 1804
    ...

ASDF and YAML Header
====================

.. code-block:: yaml

    #ASDF 1.0.0
    #ASDF_STANDARD 1.6.0
    %YAML 1.1
    %TAG ! tag:stsci.edu:asdf/
    %TAG !qiskit! asdf://qiskit.org/asdf/tags/
    %TAG !aardvark! asdf://aardvark.org/asdf/tags/

The first part, the header, is there for ASDF to keep track of the ASDF standard
used for the file, the YAML version, and aliases for YAML tags. This will always
be present, and you can ignore it most of the time.

Experiment Identifiers and ASDF properties
==========================================

.. code-block:: yaml

    --- !core/asdf-1.1.0
    uuid: !qiskit!core/uuid-0.0.0 3b620d7d7d024a01b2b62f25988b3461
    date_created: 2026-11-14 00:12:12.927647+00:00
    description: null
    asdf_library: !core/software-1.0.0 {author: The ASDF Developers, homepage: 'http://github.com/asdf-format/asdf',
      name: asdf, version: 5.0.0}
    history:
    extensions:
    - !core/extension_metadata-1.0.0
      ...

The next part starts the core of the ASDF file, where our data is stored. We
find the unique identifier for our experiment ``uuid``. The tag
``!qiskit!core/uuid-0.0.0`` is part of ASDF Qiskit, the ASDF library for
Aardvark. It tells ASDF and YAML libraries that this entry is a :class:`UUID`
instance. Then we have the date the experiment was created and a description of
our experiment (which we didn't set).

Entries ``asdf_library``, ``history``, and ``extensions`` are part of ASDF. As
an end-user of Aardvark, you do not need to deal with these. They track which
ASDF extensions were used to create the file and any modifications that may have
been made.


Artifacts
=========

.. code-block:: yaml

    artifacts: !aardvark!core/artifacts-0.0.0
        fig1.pdf: {source: fig1.pdf}

Aardvark tracks artifacts in two ways, distinguishing between artifacts bound to
a dataclass attribute and those that are associated with the experiment, called
floating artifacts. Floating artifacts are tracked in the ``artifacts`` entry of
the ASDF file, and their information is accessible in
:attr:`Experiment.artifacts`. Here we have the figure we saved. The information
says it is saved into ``fig1.pdf`` and has the same name. We an set the name to
something else in our Experiment definition as follows:

.. code-block:: python

    exp.savefig(fig, "fig1.pdf", name="figure1", description="A very nice figure.")

This results in the following in our ASDF file.

.. code-block:: yaml

    artifacts: !aardvark!core/artifacts-0.0.0
        figure1: {description: A very nice figure., source: fig1.pdf}

Dataclass attributes
====================

.. code-block:: yaml

    energies: !core/ndarray-1.1.0
        byteorder: little
        datatype: float64
        shape: [100]
        source: 0
    metrics: !aardvark!core/artifact-0.0.0 {format: npz, source: metrics_over_time.npz}
    params: [0.5, 0.5]
    t_steps: [0.0, 0.1111111111111111, 0.2222222222222222, 0.3333333333333333, 0.4444444444444444,
      0.5555555555555556, 0.6666666666666666, 0.7777777777777777, 0.8888888888888888,
      1.0]
    ...

Next come the rest of our data, which we stored in the attributes of our
experiment dataclass: ``energies``, ``metrics``, ``params``, and ``t_steps``.
The first entry, ``energies`` is a Numpy array stored inside the ASDF file and
not as an artifact. ASDF provides some metadata on the type of Numpy array as
well. The ``source: 0`` attribute of ``energies`` says that the data is stored
in the 0th block of this ASDF file. We'll cover this in the next section.

``metrics`` is a bound artifact and thus has a ``source`` and format. The format
tells us the type of file and ``source`` tells us the name of the file in which
the data is saved. The last two entries, ``params`` and ``t_steps`` are lists of
floats, a standard YAML type. Therefore, they are stored in plain-text in the
ASDF/YAML tree. The three dots signify the end of the YAML tree and the start of
the binary blocks, a feature of ASDF files.

Binary blocks
=============

ASDF supports storing binary data, i.e., Numpy arrays, inside ASDF files
themselves. They are referred to as blocks and are typically found at the end of
an ASDF file. They can also be stored in separate ASDF files, called exploded
files. We will not cover this here, but you can find more in the ASDF
documentation.

The blocks store the raw binary data for Numpy arrays found inside the file,
such as ``energies`` from earlier. The source for ``energies`` was the integer
0, which means that the first block of this file contains the binary data for
the ``energies`` Numpy array.

.. [1] See :doc:`currently supported data types <supported_types>` for details on
    which types can be saved with Aardvark. Also note :doc:`which cannot be saved
    <unsupported_types>`.
