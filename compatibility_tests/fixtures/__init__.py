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
