# This code is part of Aardvark.
#
# Copyright 2024-2025 Conrad Haupt <conrad@conradhaupt.com> and IBM.
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

import tempfile as Temp
from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID

import ddt
from aardvark.storage import FolderProvider
from aardvark.utils.tests import TestCase

from aardvark import Experiment, dataclass

DUMMY_UUID = UUID(hex="83cff1b092b24f548befbbdf08fd416c")
DUMMY_DATETIME = datetime.now(tz=timezone.utc)


@dataclass(kw_only=True)
class MockExperiment(Experiment):
    tree1: int
    tree2: dict[str, str]


def get_experiment() -> MockExperiment:
    _instance = MockExperiment(
        tree1=0,
        tree2={"A": "A", "B": "B"},
    )
    _instance.uuid = DUMMY_UUID
    _instance.set_date_created(DUMMY_DATETIME)
    return _instance


def get_experiment_and_root_dir() -> tuple[MockExperiment, str]:
    root_dir = Temp.mkdtemp(prefix="aardvark_tests_")
    provider = FolderProvider()
    _instance = get_experiment()
    _instance._context = provider.new_context()
    return _instance, root_dir


@ddt.ddt
class TestExperimentASDF(TestCase):
    """Test Experiment is saved to an ASDF file with the correct formatting.

    These tests relate to the Experiment schema, which enforces property
    ordering.
    """

    def test_asdf_property_order(self):
        exp = get_experiment()
        _file = BytesIO()
        exp._tree.write_to(_file)
        _asdf_str = str(_file.getvalue(), encoding="utf8")
        _idx_uuid = _asdf_str.index("uuid:")
        _idx_date_created = _asdf_str.index("date_created:")
        _idx_asdf_library = _asdf_str.index("asdf_library:")
        _idx_history = _asdf_str.index("history:")
        self.assertLess(_idx_uuid, _idx_date_created)
        self.assertLess(_idx_date_created, _idx_asdf_library)
        self.assertLess(_idx_asdf_library, _idx_history)

    def test_serialisation_uuid_date_created(self):
        exp = get_experiment()
        _file = BytesIO()
        exp._tree.write_to(_file)
        _asdf_str = str(_file.getvalue())
        self.assertTrue("uuid: !qiskit!core/uuid" in _asdf_str)
        self.assertTrue("date_created: {}".format(str(DUMMY_DATETIME)) in _asdf_str)
