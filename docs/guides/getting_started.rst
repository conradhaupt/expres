.. _guides_getting_started:

Getting Started
###############

Experiments with Aardvark are defined in a dataclass. Fields of the dataclass
define attributes of an experiment that will be saved to an ASDF file. All
supported classes and data types will be saved to the file, and are loadable
later. Some attributes can be marked as artifacts, these are called bound
artifacts as they are bound to a dataclass attribute. Artifacts are saved as
separate files alongside the ASDF file. Other artifacts can be created, too,
without binding them to an attribute: these are called floating artifacts.


Defining an experiment
**********************

A typical experiment starts by defining the data we want to record. An
experiment is a dataclass that inherits from :class:`aardvark.Experiment`.

.. code-block:: python

   from aardvark import Experiment, dataclass, field, artifact
   import numpy as np
   import numpy.typing as npt

   @dataclass
   class Simulation(Experiment):

      x_in: int
      params: list[float]
      results: list[npt.NDArray[np.float64]] | None = field(default=None)

      img: npt.NDArray[np.float64] | None = artifact(default=None, format="npz")

Here we have defined an experiment called ``Simulation``. It has four
attributes: ``x_in``, ``params``, ``results``, ``img``. As with
:func:`~dataclasses.dataclass`, each has a declared type. Because ``results``
and ``img`` are `optional`, in that they can also be None, we set their defaults
to ``None`` with :func:`~aardvark.dataclasses.field` and
:func:`~aardvark.dataclasses.artifact`, respectively. ``results`` will be
``None`` on object creation, but can be set later. The same is true for ``img``,
except that it will be saved as an artifact, a separate file, instead of in the
ASDF file. We need to tell Aardvark how to save this artifact, so we set the
format to ``"npz"``, which will use :func:`~numpy.savez_compressed` to save the
data, if it is not ``None``.

Saving an experiment
********************

We can save an experiment by calling :meth:`~aardvark.Experiment.save` on our object.

.. code-block:: python

   if __name__ == "__main__":
      # Create an experiment instance and set some parameters
      exp = Simulation(x_in=10, params=[0.0, 1.5, 2.75, 3.14159])
      exp.results = run_simulations()

      exp.img = load_image(exp.results)

      # This saves the experiment to our computer
      exp.save()

When our experiment is saved, our experiment attributes are saved to an ASDF
file and our artifacts are saved to files in the same folder. The specific
folder is determined by Aardvark.

Saved folder structure
======================

By default, Aardvark saves experiments into subfolders of the current directory.
There is one subfolder per experiment instance, named after the experiment class
and the experiment's metadata. The ASDF file and artifacts are saved within the
subfolder. The following is an example directory tree for a script
``simulations.py`` and the saved data. ::

   .
   ├── simulations.py
   ├── Simulation_20260113_2342_c82f6a1d
   │   ├── img.npz
   │   └── Simulation_20260113_2342_c82f6a1d.asdf
   ├── Simulation_20260113_2359_b3dd9637
   │   ├── img.npz
   │   └── Simulation_20260113_2359_b3dd9637.asdf
   └── Simulation_20260114_0012_3b620d7d
       ├── img.npz
       └── Simulation_20260114_0012_3b620d7d.asdf

The root directory can be set with a config, see :doc:`Configuration
<configuration>`, as well as the format of the folder names and ASDF filenames.

Loading a saved experiment
**************************

Say we've run our experiment and saved it to a folder in the current directory.
Now we want to plot our results with another script. We need our experiment
definition, so we import it from our script. It could also be defined somewhere
else.

.. code-block:: python

   from .simulation import Simulation
   import matplotlib.pyplot as plt

   # We load the experiment from the ASDF file, not the folder.
   exp = Simulation.load("./Simulation_20260113_2359_b3dd9637/Simulation_20260113_2359_b3dd9637.asdf")

   fig, ax = plt.subplots(2, 2)
   # Plot my figure
   ...

   # Save my figure. As exp was loaded from a file, it will be saved when
   # `savefig` is called.
   exp.savefig(fig, "fig1.pdf")


   # If we save many figures, we should postpone saving the experiment to reduce
   # the number of writes to disk.
   exp.savefig(fig2, "fig2.pdf", postpone_save=True)
   exp.savefig(fig3, "fig3.pdf", postpone_save=True)
   exp.savefig(fig4, "fig4.pdf", postpone_save=True)
   exp.save()
