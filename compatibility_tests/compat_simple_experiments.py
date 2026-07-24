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

from aardvark import Experiment, dataclass
from pytest_aardvark_fixtures import assert_tree_match, save_fixture


@dataclass(kw_only=True)
class MockExperiment(Experiment):
    field1: int
    field2: tuple[float, ...]
    arr1: np.ndarray[tuple[int], np.dtype[np.floating]]
    arr2: np.ndarray[tuple[int, int], np.dtype[np.complex128]]


@pytest.fixture()
@save_fixture
def _simple_experiment(mock_default_factories) -> MockExperiment:

    inst = MockExperiment(
        field1=0,
        field2=(0.0, 0.1, 0.2, 0.3),
        arr1=np.array([3.1415]),
        arr2=np.array([[1.0, 1.0j], [-1.0j, 1.0]]),
    )

    return inst


def compat_simple_experiment(
    _simple_experiment: MockExperiment,
    saved_fixtures: dict[str, Any],
    mock_default_factories,
):
    _msg = "Loaded experiment is incorrect.".format(str(_simple_experiment))

    _expected_tree = _simple_experiment
    _loaded_tree = saved_fixtures["_simple_experiment"]
    # assert _simple_experiment == saved_fixtures["_simple_experiment"], _msg
    assert_tree_match(
        old_tree=_expected_tree._tree._tree, new_tree=_loaded_tree._tree._tree
    )
