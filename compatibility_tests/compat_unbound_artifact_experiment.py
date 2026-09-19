# This code is part of Aardvark.
#
# Copyright 2024-2026 Conrad Haupt <conrad@conradhaupt.com> and IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any

import pytest

from aardvark.storage.folder_provider import FolderContext
from pytest_aardvark_fixtures import assert_tree_match, save_fixture

from aardvark import Experiment, dataclass


@dataclass(kw_only=True)
class MockExperiment(Experiment):
    field1: int
    field2: tuple[float, ...]


@pytest.fixture(scope="module")
@save_fixture
def _unbound_artifact_experiment(mock_default_factories) -> MockExperiment:
    from uuid import uuid4

    import matplotlib as mpl
    import matplotlib.pyplot as plt

    inst = MockExperiment(field1=0, field2=(0.0, 0.1, 0.2, 0.3))
    mpl.use("pdf")
    fig, ax = plt.subplots(1, 1)
    ax.plot([0, 1], [1, -1])
    ax.set_xlabel("X values")
    ax.set_ylabel("Y values")
    inst.savefig(
        fig,
        file="myfigure.png",
        name="figure",
    )

    return inst


def compat_simple_experiment(
    _unbound_artifact_experiment: MockExperiment,
    saved_fixtures: dict[str, Any],
    mock_default_factories,
):
    from matplotlib.testing import compare as mpl_compare

    _msg = "Loaded experiment is incorrect.".format(str(_unbound_artifact_experiment))

    _expected_tree = _unbound_artifact_experiment
    _loaded_tree = saved_fixtures["_unbound_artifact_experiment"]
    assert_tree_match(
        old_tree=_expected_tree._tree._tree, new_tree=_loaded_tree._tree._tree
    )

    # *** Check that both figures are the same
    # Assert we have figure artifacts
    assert _expected_tree.artifacts.exists_for(name="figure"), (
        "Expected experiment does not have the figure artifact"
    )
    assert _loaded_tree.artifacts.exists_for(name="figure"), (
        "Loaded experiment does not have the figure artifact"
    )
    # Assert that the files actually exist.
    _expected_context: FolderContext = _expected_tree._context
    _expected_artifact_path = _expected_context.get_artifact_path(name="figure")
    _loaded_context: FolderContext = _loaded_tree._context
    _loaded_artifact_path = _loaded_context.get_artifact_path(name="figure")
    assert _expected_artifact_path.exists(), (
        f"Expected tree's artifact file does not exist: {_expected_artifact_path}"
    )
    assert _loaded_artifact_path.exists(), (
        f"Loaded tree's artifact file does not exist: {_loaded_artifact_path}"
    )

    _compare_res = mpl_compare.compare_images(
        str(_expected_artifact_path),
        str(_loaded_artifact_path),
        tol=1e-9,
        in_decorator=False,
    )

    assert _compare_res is None, f"Figure artifacts differ: reason={_compare_res!r}"
