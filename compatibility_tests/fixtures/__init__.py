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

import unittest.mock as mock
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest


@pytest.fixture(scope="session", autouse=True)
def mock_default_factories():
    """Mock default factories for :class:`Experiment`.

    To work correctly, ``mock_default_factories`` must be included as a
    parameter in the test and fixture functions.

    Default Values:
        uuid: ``UUID(hex="3f4b3306-ac5f-4066-9d5c-c82ac0f6203a")``
        date_created: ``datetime(2063, 4, 5, 17, 1, 0, "America/Denver")``
    """
    _fixed_uuid = UUID(hex="3f4b3306-ac5f-4066-9d5c-c82ac0f6203a")
    _fixed_datetime = datetime(2063, 4, 5, 17, 1, 0, tzinfo=ZoneInfo("America/Denver"))
    with mock.patch.multiple(
        "aardvark.experiment.experiment",
        new_uuid=mock.MagicMock(return_value=_fixed_uuid),
        current_datetime=mock.MagicMock(return_value=_fixed_datetime),
    ):
        yield
