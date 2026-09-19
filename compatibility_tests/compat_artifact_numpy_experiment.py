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

import numpy as np
import pytest

from pytest_aardvark_fixtures import assert_tree_match, save_fixture

from aardvark import Experiment, artifact, dataclass


@dataclass(kw_only=True)
class MockExperiment(Experiment):
    field1: int
    field2: tuple[float, ...]

    art1: np.ndarray[tuple[int], np.dtype[np.floating]] = artifact(format="npz")


@pytest.fixture(scope="module")
@save_fixture
def _artifact_experiment(mock_default_factories) -> MockExperiment:
    from uuid import uuid4

    inst = MockExperiment(
        field1=0, field2=(0.0, 0.1, 0.2, 0.3), art1=np.zeros((5, 5), dtype=np.float64)
    )

    return inst


def compat_simple_experiment(
    _artifact_experiment: MockExperiment,
    saved_fixtures: dict[str, Any],
    mock_default_factories,
):
    _msg = "Loaded experiment is incorrect.".format(str(_artifact_experiment))

    _expected_tree = _artifact_experiment
    _loaded_tree = saved_fixtures["_artifact_experiment"]
    assert_tree_match(
        old_tree=_expected_tree._tree._tree, new_tree=_loaded_tree._tree._tree
    )
