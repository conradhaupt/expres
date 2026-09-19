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
from os.path import exists
from pathlib import Path
from unittest import mock
from uuid import UUID

import ddt
import matplotlib.pyplot as plt
from aardvark.config.config import temp_config
from aardvark.storage import FolderContext, FolderProvider
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
class TestExperimentSaveLoadArtifacts(TestCase):
    """Test saving and loading Experiment instances."""

    def test_save_artifacts_with_folder_provider(self):
        """Test that floating artifacts are actually created."""
        exp, root_dir = get_experiment_and_root_dir()
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"]["root_dir"] = (
                root_dir
            )
            exp.save()

        self.assertTrue(isinstance(exp._context, FolderContext))
        asdf_path = exp._context._current_path

        log_str = "2025.01.01 00:00 This is a test\n"
        with exp.open_artifact("execution.log", "w", name="log") as f:
            f.write(log_str)
        with exp.open_artifact("execution.log", "r") as f:
            _read_str = f.read()
        self.assertEqual(_read_str, log_str)
        self.assertTrue(exists(asdf_path.parent.joinpath(Path("execution.log"))))
        with open(asdf_path.parent.joinpath(Path("execution.log"))) as f:
            _read_str = f.read()
        self.assertEqual(_read_str, log_str)

    def test_save_with_folder_provider(self):
        """Test that saving actually creates the file."""
        exp, root_dir = get_experiment_and_root_dir()
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"]["root_dir"] = (
                root_dir
            )
            exp.save()

        self.assertTrue(isinstance(exp._context, FolderContext))
        _context: FolderContext = exp._context
        actual_path = _context._current_path

        self.assertTrue(exists(actual_path))

    def test_load_with_folder_provider(self):
        """Test that saving actually creates the file."""
        exp, root_dir = get_experiment_and_root_dir()
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"]["root_dir"] = (
                root_dir
            )
            exp.save()
            exp_path = exp._context._current_path

        self.assertTrue(exp_path.exists())

        loaded_exp = MockExperiment.load(exp_path)
        self.assertEqual(
            exp,
            loaded_exp,
            msg="Loaded experiment is not the same as saved experiment.",
        )
        loaded_exp._tree.close()

    @ddt.idata(
        [
            ("just file is provided.", {"file": "artifact.txt"}),
            ("just name is provided.", {"name": "my_artifact"}),
            (
                "name and file are provided.",
                {"file": "artifact.txt", "name": "my_artifact"},
            ),
        ]
    )
    @ddt.unpack
    def test_open_existing_artifact_with_different_arguments(
        self, config_msg: str, open_kwargs
    ):
        """Test that opening an artifact with different arguments works."""
        exp, root_dir = get_experiment_and_root_dir()
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"]["root_dir"] = (
                root_dir
            )
            # We create an artifact which we will try to retrieve later.
            with exp.open_artifact(
                file="artifact.txt",
                mode="w",
                name="my_artifact",
                description="My description.",
            ) as f:
                f.write("This is a test.")
            exp.save()

        # Attempt to open the artifact and read its contents
        with exp.open_artifact(**open_kwargs, mode="r") as f:
            _data = f.read()
        self.assertEqual(
            _data,
            "This is a test.",
            msg="Artifact contents isn't as expected when {}.".format(config_msg),
        )

    @ddt.idata(
        [
            ("just file is provided.", {"file": "artifact.txt"}),
            ("just name is provided.", {"name": "my_artifact"}),
            (
                "name and file are provided.",
                {"file": "artifact.txt", "name": "my_artifact"},
            ),
        ]
    )
    @ddt.unpack
    def test_write_existing_artifact_with_different_arguments(
        self, config_msg: str, open_kwargs
    ):
        """Test that writing to an existing artifact, with different open_artifact arguments, works."""
        exp, root_dir = get_experiment_and_root_dir()
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"]["root_dir"] = (
                root_dir
            )
            # We create an artifact which we will try to retrieve later.
            with exp.open_artifact(
                file="artifact.txt",
                mode="w",
                name="my_artifact",
                description="My description.",
            ) as f:
                f.write("This is a test.")
            exp.save()

        # Attempt to open the artifact and read its contents
        with exp.open_artifact(**open_kwargs, mode="w") as f:
            f.write("This is a new test.")
        with exp.open_artifact(**open_kwargs, mode="r") as f:
            _data = f.read()
        self.assertEqual(
            _data,
            "This is a new test.",
            msg="Artifact contents isn't as expected when {}.".format(config_msg),
        )

    @ddt.idata(
        [
            ("just png file is provided.", "png", {"file": "figure1.png"}),
            ("just name is provided.", "png", {"name": "figure1"}),
            (
                "name and png file are provided.",
                "png",
                {"file": "figure1.png", "name": "figure1"},
            ),
            # PDF files
            ("just pdf file is provided.", "pdf", {"file": "figure1.pdf"}),
            ("just name is provided.", "pdf", {"name": "figure1"}),
            (
                "name and pdf file are provided.",
                "pdf",
                {"file": "figure1.pdf", "name": "figure1"},
            ),
        ]
    )
    @ddt.unpack
    def test_save_existing_figure_with_different_arguments(
        self, config_msg: str, expected_format: str, open_kwargs
    ):
        """Test that saving a figure to an existing artifact, with different savefig arguments, works."""
        import aardvark.storage.base_provider as prov

        captured_formats = []
        original_source_to_figure_format = prov.source_to_figure_format

        def wrapper(source: str) -> str:
            _val = original_source_to_figure_format(source)
            captured_formats.append(_val)
            return _val

        with mock.patch(
            "aardvark.storage.base_provider.source_to_figure_format", wrapper
        ) as _patch:
            exp, root_dir = get_experiment_and_root_dir()
            fig = plt.figure()
            with temp_config() as _config:
                _config["storage_providers"]["folder_storage_provider"]["root_dir"] = (
                    root_dir
                )
                # We create an artifact which we will try to retrieve later.
                exp.savefig(
                    fig,
                    file="figure1.{}".format(expected_format),
                    name="figure1",
                )
                exp.save()

            self.assertEqual(
                len(captured_formats),
                1,
                msg="source_to_figure_format should have been called exactly once when {}.".format(
                    config_msg
                ),
            )
            self.assertEqual(
                captured_formats[0],
                expected_format,
                "Figure format should be {} when {}.".format(
                    expected_format, config_msg
                ),
            )

            # Attempt to save the figure again
            fig2 = plt.figure()
            exp.savefig(fig2, **open_kwargs)
            self.assertEqual(
                exp.artifacts.num_artifacts,
                1,
                msg="Number of artifacts should equal the number of figures saved, with open_artifact when {}".format(
                    config_msg
                ),
            )
