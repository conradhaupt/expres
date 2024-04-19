.. _guides_configuration:

Configuration
#############

Aardvark supports config files for changing how experiments are saved to disk.
This can be done in two ways: through a config file `.aardvark.yml` and a
:class:`~aardvark.config.Config` object.

Config Structure
****************

.. code-block:: yaml

    config_version: 0.1.0
    storage_providers:
        folder_storage_provider:
            root_dir: ./
            temp_dir: null
            folder_format: "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
            filename_format: "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}.asdf"
            description_max_length: 15

The above is the default configuration for Aardvark. The only entries in the
current version are to configure how experiments are saved with the Folder
Provider. The options are:

* ``root_dir``: The directory into which all experiments are saved. Each
  experiment will have a folder in this directory.
* ``temp_dir``: Experiments that have not been saved yet are stored in this
  directory. If ``null``, then the system's temporary directory is used. This is
  important for artifacts created before the experiment is saved. When saved,
  the artifact files are moved to the final experiment folder.
* ``folder_format``: A Python f-string that defines the name of the experiment's
  folder. See below for details on each parameter.
* ``filename_format``: A Python f-string that defines the name of the
  experiment's ASDF file. See below for details on each parameter.
* ``description_max_length``: Defines the maximum length for the parameter
  ``{desc}``.

Folder and Filename Format Strings
==================================

The ``folder_format`` and ``filename_format`` config options define how to name
an experiment's folder and ASDF file. They are treated as Python f-strings by
Aardvark. The parameters are as follows:

* ``experiment_name``: The name of the :class:`Experiment` class defined by the
  user.
* ``date_create``: The date and time when the :class:`Experiment` instance was
  created, as a :class:`datetime` instance.
* ``desc``: If the experiment has a description set, this is a truncated version
  where repeated newlines and spaces are replaced with a single underscore. The
  length of ``desc`` is controlled by ``description_max_length``. ``desc`` will
  contain an underscore as a prefix to separate it from any prior parameter in
  ``folder_format`` and ``filename_format``. If the experiment's description is
  ``None``, then ``desc`` is an empty string.
* ``uuid_short``: Each experiment has a UUID, which is 32 characters long in its
  hexadecimal representation. ``uuid_short`` is the first 8 hexadecimal
  characters of this UUID.

Changing the Configuration
**************************

Config files are loaded by Aardvark when needed. Aardvark supports two locations
for config files: in ``<user home>/.aardvark.yml`` and ``<current
directory>/.aardvark.yml``. The current directory config takes precedence over
the config in the user directory. If neither exists, or if neither defines a
specific config option, then the default is used. This is like a stack of
configs where those higher in the stack take precedence over those lower in the
stack.

During runtime, users can override or set config options using
:func:`get_config` and :func:`temp_config`. The former retrieves the current
config instance, and allows for setting config options globally. The latter,
:func:`temp_config`, returns a config in a context manager that reverts back to
the previous configuration when exited. See below for an example.

.. code-block:: python

    from aardvark import get_config, temp_config

    # We set the following config options in config files.
    # root_dir=~/ in the user's config file.
    # filename_format=myexperiment.asdf in the current directory's config file.

    # We create our experiment and set some values.
    exp = MyExperiment(...)
    exp.results = ...

    # If we save now, our experiment is saved to the following file:
    # ~/MyExperiment_<date>_<description>_<uuid_short>/myexperiment.asdf
    exp.save()

    # If we instead wanted to change the ASDF filename, we can use
    # temp_config. Note that we must do this INSTEAD of running exp.save()
    # above. If we did both, the experiment would be saved to the file from the
    # first call to .save().
    with temp_config() as _config:
        _config["storage_providers"]["folder_storage_provider"]["filename_format"] = "new_experiment.asdf"
        exp.save()

    # We can also set the location for all subsequent experiments in this
    # script.
    get_config()["storage_providers"]["folder_storage_provider"]["root_dir"] = "~/Data/Project/"
    exp_second = ...
    exp_third = ...

    # Now both of these experiments will be saved to a new root directory.
    exp_second.save()
    exp_third.save()
