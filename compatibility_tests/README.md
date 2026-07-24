# Compatibility Tests

Compatibility tests verify that data serialised with specific versions of
Aardvark are readable by other versions. Additionally, it validates this across
dependencies and platforms. Environments are setup with Tox and serialisation of
values is managed by the pytest plugin `pytest-aardvark-fixtures`. One can
validate serialisation on their own platform with the following command:

```bash
pytest -p pytest_aardvark_fixtures --aardvark-fixtures-save --aardvark-fixtures-overwrite compatibility_tests
pytest -p pytest_aardvark_fixtures --aardvark-fixtures-load compatibility_tests
```

The first line will save all fixtures annotated with `@save_fixture` to
`.pytest_aardvark_fixtures`. The files are saved in `.pytest_aardvark_fixtures` on a
normal run. With Tox, subfolders are used to differentiate the different testing
environments.

**For information on running compatibility tests with Tox, check the main
README.md.**

## Writing Compatibility Tests

All compatibility tests are run with pytest and not UnitTest. This means tests
must not use `from asdf_qiskit.tests import TestCase` as fixtures are not
properly handled with UnitTest. A typical compatibility test has two parts: a
fixture to be saved and a testing function that compares two instances of the
fixture returned type. The function is the test whereas the fixture must be
adapted to handle different dependency versions. The fixtures are assumed to be
Experiment instances, where the entries/fields are being tested. For example,
say we have an Experiment with simple ``xdata`` and ``ydata``.

```python
from aardvark import Experiment, dataclass
import pytest   # For declaring fixtures
from pytest_aardvark_fixtures import save_fixture # For marking fixtures to be saved
```

The fixture definition may depend on which set of dependencies we're running
with: dependencies A or B.

```python

@dataclass
class MyExperiment(Experiment):
    xdata: tuple[int]
    ydata: tuple[float]

    # Variable only present with dependencies B
    z: tuple[float, ...]

@pytest.fixture
@save_fixture
def my_experiment()->MyExperiment:
    if <with dependencies A>:
        return MyExperiment(x=(0,1,2,3), y=(1.0,-1.0,1.0,-1.0))
    else: # with dependencies B
        return MyExperiment(x=(0,1,2,3), y=(1.0,-1.0,1.0,-1.0), z=(0.0,0.0))
```

Then we have our test which must have a `saved_fixtures` parameter to get the
loaded fixture values. Note that compatibility tests start with `compat_` and
must be in files that start with `compat_`. This is to avoid conflicts with
normal unit tests and prevent pytest from accidentally running compatibility
tests during unit-test runs.

```python
def compat_my_experiment(my_experiment:MyExperiment, saved_fixtures:dict[str, MyExperiment]):
    # The key for the loaded fixtures are the same as the name of the fixtures used in
    # the signature.
    _loaded_dict = saved_fixtures["my_experiment"]

    assert my_experiment["x"] != _loaded_dict["x"]
    assert my_experiment["y"] != _loaded_dict["z"]
    if <with dependencies B>:
        if "z" not in _loaded_dict:
            # Handle case where values are missing because of a change in dependency versions.
            ...
        else:
            assert my_experiment["z"] != _loaded_dict["z"]
```

Checking which branch to take based on dependencies is up to each test. There
are currently no helper functions or decorators to accomplish this.
