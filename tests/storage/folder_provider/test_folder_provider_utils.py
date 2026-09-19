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

import unittest.mock as mock
from datetime import datetime
from datetime import timezone as tz
from pathlib import Path
from uuid import UUID

from aardvark.storage.folder_provider import (
    target_path_for,
    transformed_description,
)
from aardvark.utils.tests.config_test_case import (
    MockConfigTestCase,
    patch_multiple_configs,
)

from aardvark import Experiment, dataclass

DUMMY_GLOBAL_CONFIG_YAML = """# This part of the config file should not be changed by users. When a config
# file is loaded by aardvark, it should automatically be updated and saved in
# newer versions.
config_version: 0.1.0

# Aardvark will support multiple ways of saving experiments. The only provider
# right now is FolderProvider, which saves experiment instances in their own
# folder, alongside artifacts.
storage_providers:
  # FolderProvider configuration values.
  folder_storage_provider:
    # Root directory for all experiments.
    root_dir: "/home/user/Data"
    # Python format string for the ASDF filename.
    filename_format: "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}.asdf"
    # Python format string for the experiment folder, in which the ASDF file and
    # artifacts will be saved.
    folder_format: "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
    # Number of characters in {desc}
    description_max_length: 25
"""
DUMMY_LOCAL_CONFIG_YAML = """
storage_providers:
  folder_storage_provider:
    folder_format: "TEST_FOLDER_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
"""
DUMMY_UUID = UUID(hex="83cff1b092b24f548befbbdf08fd416c")
DUMMY_DATETIME = datetime.now(tz=tz.utc)


@dataclass
class MockExperiment(Experiment):
    tree1: int
    tree2: float

    def __post_init__(self):
        super().__post_init__()
        self.date_created = DUMMY_DATETIME
        self.uuid = DUMMY_UUID


# We patch __must_init_config_context so we always reinitialise the Config
# ContextVar. This forces the Config to call global_config and local_config_for.
@mock.patch("aardvark.config.config.__must_init_config_context", new=lambda: True)
class TestFolderProvider_TargetPathFor(MockConfigTestCase):
    """ "Test :fun:`target_path_for` for :class:`FolderProvider`."""

    def expected_path(
        self,
        experiment_name: str,
        date_created: datetime,
        description: str | None,
        uuid: UUID,
        folder_format: str | None = None,
        filename_format: str | None = None,
    ) -> Path:
        """Return a :class:`Path` for the given parameters

        Args:
            experiment_name: The experiment name.
            date_created: The date the experiment was created.
            description: The description of the experiment.
            uuid: The :class:`UUID` of the experiment

        Returns:
            The expected target path for this experiment, when saved.
        """
        if folder_format is None:
            folder_format = "TEST_FOLDER_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
        if filename_format is None:
            filename_format = (
                "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}.asdf"
            )
        format_kwargs = {
            "experiment_name": experiment_name,
            "date_created": date_created,
            "desc": transformed_description(description=description, max_length=25),
            "uuid_short": uuid.hex[:8],
        }
        expected_folder_name = folder_format.format(**format_kwargs)
        expected_filename = filename_format.format(**format_kwargs)
        expected_root_dir = "/home/user/Data"
        return Path(expected_root_dir).joinpath(
            Path(expected_folder_name), Path(expected_filename)
        )

    # TODO:Move these tests to test_folder_storage.py
    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            global_config_yaml=DUMMY_GLOBAL_CONFIG_YAML,
            local_config_yaml=DUMMY_LOCAL_CONFIG_YAML,
        ),
    )
    def test_target_path_for_experiment_from_config(self):
        """Test target_path_for with an experiment and format strings from the config file."""
        experiment = MockExperiment(
            tree1=0, tree2=0.0, description="This is a description."
        )
        expected_path = self.expected_path(
            experiment_name=experiment.__class__.__name__,
            date_created=DUMMY_DATETIME,
            description=experiment.description,
            uuid=experiment.uuid,
        )
        actual_path = target_path_for(experiment=experiment)
        self.assertEqual(expected_path, actual_path)

    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            global_config_yaml=DUMMY_GLOBAL_CONFIG_YAML,
            local_config_yaml=DUMMY_LOCAL_CONFIG_YAML,
        ),
    )
    def test_target_path_for_experiment_with_overrides(self):
        """Test target_path_for with an experiment and format strings as arguments."""
        experiment = MockExperiment(
            tree1=0, tree2=0.0, description="This is a description."
        )
        folder_format = (
            "DUMMY_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
        )

        filename_format = (
            "DUMMY_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}.asdf"
        )

        expected_path = self.expected_path(
            experiment_name=experiment.__class__.__name__,
            date_created=DUMMY_DATETIME,
            description=experiment.description,
            uuid=experiment.uuid,
            filename_format=filename_format,
            folder_format=folder_format,
        )
        actual_path = target_path_for(
            experiment=experiment,
            filename_format=filename_format,
            folder_format=folder_format,
        )
        self.assertEqual(expected_path, actual_path)

    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            global_config_yaml=DUMMY_GLOBAL_CONFIG_YAML,
            local_config_yaml=DUMMY_LOCAL_CONFIG_YAML,
        ),
    )
    def test_target_path_for_asdffile_from_config(self):
        """Test target_path_for with an AsdfFile and format strings from the config file."""
        experiment = MockExperiment(
            tree1=0, tree2=0.0, description="This is a description."
        )
        expected_path = self.expected_path(
            # This is important for this test as we want to verify
            # target_path_for works with an AsdfFile. AsdfFiles get an
            # experiment name of "Experiment".
            experiment_name="Experiment",
            date_created=DUMMY_DATETIME,
            description=experiment.description,
            uuid=experiment.uuid,
        )
        actual_path = target_path_for(
            # This is important for this test as we want to verify
            # target_path_for works with an AsdfFile. We get this from
            # Experiment._tree.
            experiment=experiment._tree,
        )
        self.assertEqual(expected_path, actual_path)

    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            global_config_yaml=DUMMY_GLOBAL_CONFIG_YAML,
            local_config_yaml=DUMMY_LOCAL_CONFIG_YAML,
        ),
    )
    def test_target_path_for_asdffile_with_overrides(self):
        """Test target_path_for with an AsdfFile and format strings as arguments."""
        experiment = MockExperiment(
            tree1=0, tree2=0.0, description="This is a description."
        )
        folder_format = (
            "DUMMY_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
        )

        filename_format = (
            "DUMMY_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}.asdf"
        )

        expected_path = self.expected_path(
            # This is important for this test as we want to verify
            # target_path_for works with an AsdfFile. AsdfFiles get an
            # experiment name of "Experiment".
            experiment_name="Experiment",
            date_created=DUMMY_DATETIME,
            description=experiment.description,
            uuid=experiment.uuid,
            filename_format=filename_format,
            folder_format=folder_format,
        )
        actual_path = target_path_for(
            # This is important for this test as we want to verify
            # target_path_for works with an AsdfFile. We get this from
            # Experiment._tree.
            experiment=experiment._tree,
            filename_format=filename_format,
            folder_format=folder_format,
        )
        self.assertEqual(expected_path, actual_path)
