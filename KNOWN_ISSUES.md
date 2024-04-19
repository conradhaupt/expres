# Known Issues with Aardvark

## Aardvark

1. `field(default=..., init=False)` attributes are not saved to the ASDF file on
   instantiation.

    - `@dataclass` generates an `__init__` method if it doesn't already exist.
     Fields/attributes with default values are set in this generated `__init__`
     method. If the default is set with `field(default=value)`, then the
     signature will have `__init__(self,...,attr=value)`. If the default is set
     with `default_factory`, then the body of `__init__` will set the attribute
     value with a call to the factory. However, if `init=False` is set, then **only default factories are set in the generated `__init__` method.**

     Therefore, the default values for non-init attributes are set with a
     descriptor-type object. This means that there is never a call to
     `__setattr__` for default values with `init=False`.

   - **Workarounds:** One can use `field(default_factory=lambda: default_value)`
     instead, which is definitely called in the body of the generated `__init__`
     method. Or, one can keep `init=True` (the default for `field`).

   - **Possible solutions:** Add a method that is called once and only once in
     `__post_init__` which checks for fields in `__dataclass_fields__` that
     (i) are not registered in the ASDF file and (ii) have a default value, then
     set them.

2. ArtifactCollection does not allow for artifacts with the same name. However,
   in principle this is possible with bound and floating artifacts. Consider the
   following Experiment saved as YAML:

   ```yaml
   x_vals: !ndarray
     source: 0
   y_vals: !ndarray
     source: 1
   z_vals: !artifact_info
     source: swept_z_vals.npz
   artifacts: !artifacts
     z_vals:
       source: z_vals.npy
    ```

   In this scenario we have two artifacts with the name `z_vals`. **It is
   unclear if this is something Aardvark should support.**

3. Experiment does not handle closing ASDF files. `Experiment` currently loads
   an ASDF file and calls `AsdfFile.write_to`, but never `AsdfFile.close()`.
   This has not been an issue thus far as `Experiment` is targetting scripts
   where a file is only ever opened once. However, a warning in tests indicates
   that this is a problem. For example, the following test will raise a warning
   which pytest captures and raises as an error:

   ```python
   def test_save_load(self):
    exp = self.get_new_experiment()
    # Do some stuff
    exp.save()

    load_exp = MyExp.load(exp._context._current_path)
    # Do some more stuff
    ...

    # Following warning raised:
    # ResourceWarning: unclosed file <_io.FileIO name='<file>.asdf' mode='rb' closefd=True>
   ```

    The reason for this warning is that both `exp` and `load_exp` have files
    pointing to the same ASDF file. During garbage collection, which PyTest
    calls multiple times during test cleanup, warnings are raised that the files
    were never closed. `AsdfFile.close()` would solve this, but the workflow
    with `Aardvark` is not clear. For example, should `Experiment.close()`
    disable `__setattr__` and `__getattribute__`? `AsdfFile.close()` will clear
    the tree, resulting in an empty AsdfFile after closing. This isn't possible
    with `Experiment` as we have defined attributes which do not have an "empty"
    value.
