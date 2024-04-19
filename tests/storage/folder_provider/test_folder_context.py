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

import os
from datetime import datetime
from datetime import timezone as tz
from pathlib import Path
from tempfile import mkdtemp
from uuid import UUID

import ddt
from aardvark.artifacts.artifact import ArtifactInfo
from aardvark.artifacts.artifact_collection import ArtifactCollection
from aardvark.config import get_config
from aardvark.storage.base_provider import BaseContext, ContextState
from aardvark.storage.folder_provider import (
    FolderContext,
    FolderProvider,
    format_path,
    target_path_for,
    transformed_description,
)
from aardvark.utils.tests import TestCase

from aardvark import Experiment, dataclass, temp_config

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


@ddt.ddt
class TestFolderContext(TestCase):
    """Test FolderContext"""

    def setUp(self) -> None:
        super().setUp()
        self._home = None

    def get_experiment(self, context: BaseContext | None = None):
        kwargs = {}
        if context is not None:
            kwargs["context"] = context
        _exp = MockExperiment.__new__(MockExperiment, **kwargs)
        _exp.__init__(tree1=1, tree2=3.14159)
        return _exp

    def mkdtemp_root_dir_with_home(self, prefix: str) -> tuple[Path, str]:
        """Create a temporary directory and two paths to the directory.

        The first path is the absolute path with :meth:`expanduser`. This is the
        expected path for an experiment. The second path is what the user sets
        as the root directory for FolderContext. If :attr:`_home` is None, this
        is a temporary directory defined by the system being tested. If
        :attr:`_home` is not None, then we assume the user is setting the root
        directory as ``"~/<some folder>"``. In this case we would need to
        replace "~" with :attr:`_home`. This should be done by setting the
        ``"HOME"`` environment variable in :meth:`setUp`.

        Args:
            prefix: Prefix for the temporary folder.

        Returns:
            Tuple ``(abs, user)`` where ``abs`` is the expected path to the root
            directory for a FolderContext instance. ``user`` is the string the
            user provides to ``"root_dir"`` in their config instance or YAML
            file.
        """
        _temp_dir = Path(
            mkdtemp(
                prefix=prefix,
                dir=self._home,
            )
        )
        if self._home is None:
            _tmp_dir = _temp_dir.parent
        else:
            _tmp_dir = Path("~")

        _mkdtemp_abs = _temp_dir.absolute()
        _mkdtemp_user = _tmp_dir.joinpath(_mkdtemp_abs.name)
        return _mkdtemp_abs, str(_mkdtemp_user)

    def test_new_unsaved_context(self):
        """Test the default new context for FolderProvider."""
        expected_root_dir, user_root_dir = self.mkdtemp_root_dir_with_home(
            prefix="aardvark_test"
        )
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "temp_dir"
            ] = user_root_dir
            provider = FolderProvider()
            context = provider.new_context()

        # Check that the initial values are correct
        self.assertEqual(
            context._state,
            ContextState.unsaved,
            "New unsaved context has the wrong state.",
        )
        self.assertEqual(
            context._current_path.parent.parent,
            expected_root_dir,
            msg="Unsaved context is not saving to the temporary directory.",
        )
        self.assertEqual(
            context._artifacts_to_move,
            set(),
            msg="New unsaved context should not have any artifacts to move.",
        )

    def test_saved_experiment_context(self):
        """Test that an experiment is saved correctly using its builtin context."""
        expected_root_dir, user_root_dir = self.mkdtemp_root_dir_with_home(
            prefix="aardvark_test"
        )
        provider = FolderProvider()
        _context = provider.new_context()

        # *** 'save' an experiment
        experiment: MockExperiment = self.get_experiment(context=_context)
        config = get_config()
        expected_path = target_path_for(
            experiment=experiment,
            folder_format=config["storage_providers"]["folder_storage_provider"][
                "folder_format"
            ],
            filename_format=config["storage_providers"]["folder_storage_provider"][
                "filename_format"
            ],
            root_dir=str(expected_root_dir),
        )

        # Save experiment
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = user_root_dir
            self.assertEqual(
                get_config()["storage_providers"]["folder_storage_provider"][
                    "root_dir"
                ],
                user_root_dir,
                msg="Setting root_dir did not change value for get_config().",
            )
            experiment.save()

        # Check context values
        self.assertEqual(
            experiment._context._current_path,
            expected_path,
            msg="Current path of FolderContext is not as expected.",
        )
        self.assertEqual(
            experiment._context._state,
            ContextState.saved,
            msg="Saved experiment state must be ContextState.saved.",
        )
        self.assertTrue(expected_path.exists(), msg="Saved experiment does not exist.")

        # Check that saved experiment is correct.
        loaded_experiment = MockExperiment.load(expected_path)
        self.assertEqual(loaded_experiment, experiment)
        self.assertEqual(loaded_experiment.uuid, experiment.uuid)
        self.assertEqual(loaded_experiment.date_created, experiment.date_created)
        self.assertEqual(loaded_experiment.tree1, experiment.tree1)
        self.assertEqual(loaded_experiment.tree2, experiment.tree2)
        self.assertTrue(loaded_experiment._context, experiment._context)
        loaded_experiment._tree.close()

    def test_saved_asdffile_context(self):
        """Test that an asdffile is saved correctly using its builtin context."""
        expected_root_dir, user_root_dir = self.mkdtemp_root_dir_with_home(
            prefix="aardvark_test"
        )
        provider = FolderProvider()
        _context = provider.new_context()

        # *** 'save' an experiment
        experiment = self.get_experiment(context=_context)
        tree = experiment._tree
        context: FolderContext = experiment._context
        config = get_config()
        expected_path = target_path_for(
            experiment=tree,
            folder_format=config["storage_providers"]["folder_storage_provider"][
                "folder_format"
            ],
            filename_format=config["storage_providers"]["folder_storage_provider"][
                "filename_format"
            ],
            root_dir=str(expected_root_dir),
        )

        # Save experiment
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = user_root_dir
            context.save(experiment=tree)

        # Check context values
        self.assertEqual(
            context._current_path,
            expected_path,
            msg="Current path of FolderContext is not as expected.",
        )
        self.assertEqual(
            experiment._context._state,
            ContextState.saved,
            msg="Saved experiment state must be ContextState.saved.",
        )
        self.assertTrue(expected_path.exists(), msg="Saved experiment does not exist.")

        # Check that saved experiment is correct.
        loaded_tree, loaded_context = FolderContext.load(expected_path)
        # We ignore the following tree keys as they are added by AsdfFile.write_to()
        ignored_asdf_keys = [
            "history",
            "asdf_library",
            # We ignore it in this test, but should be testing it somewhere
            # else.
            "artifacts",
        ]
        self.assertEqual(
            {k for k in loaded_tree.keys() if k not in ignored_asdf_keys},
            set(tree.keys()),
        )
        for k in tree.keys():
            self.assertEqual(
                loaded_tree[k],
                tree[k],
                msg="Loaded tree[{!r}] from context not as expected.".format(k),
            )
        self.assertEqual(loaded_tree["uuid"], tree["uuid"])
        self.assertEqual(loaded_tree["date_created"], tree["date_created"])
        self.assertEqual(loaded_tree["tree1"], tree["tree1"])
        self.assertEqual(loaded_tree["tree2"], tree["tree2"])
        self.assertEqual(context, loaded_context)
        loaded_tree.close()
        tree.close()
        experiment._tree.close()

    def test_saved_context(self):
        """Test that an experiment is saved correctly using a separate context."""
        expected_root_dir, user_root_dir = self.mkdtemp_root_dir_with_home(
            prefix="aardvark_test"
        )
        provider = FolderProvider()
        context: FolderContext = provider.new_context()

        # *** 'save' an experiment
        experiment = self.get_experiment()

        # Get expected values NOTE: This must be updated when
        # `FolderContext._folder_name_for` and `FolderContext._filename_for` are
        # updated.
        format_kwargs = {
            "date_created": DUMMY_DATETIME,
            "experiment_name": MockExperiment.__name__,
            "uuid": DUMMY_UUID,
            "description": experiment.description,
        }

        # Save experiment
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = user_root_dir
            expected_path = format_path(
                **format_kwargs, root_dir=str(expected_root_dir)
            )
            context.save(experiment=experiment, overwrite=False)

        # Double check we processed the path correctly.
        self.assertEqual(
            expected_root_dir,
            expected_path.parent.parent,
            msg="Root dir is not as expected from format_path.",
        )
        # Check the context path is correct.
        self.assertEqual(
            context._current_path.parent.parent,
            expected_root_dir,
            msg="Root dir from context is incorrect.",
        )
        self.assertEqual(
            context._current_path.parent,
            expected_path.parent,
            msg="Experiment folder path from context is incorrect.",
        )
        self.assertEqual(
            context._current_path, expected_path, msg="Path to experiment is incorrect."
        )
        self.assertTrue(expected_path.exists(), msg="Saved experiment doesn't exist.")
        self.assertEqual(
            context._state,
            ContextState.saved,
            msg="Saved experiment state must be ContextState.saved.",
        )

        # Check that saved experiment is correct.
        loaded_experiment = MockExperiment.load(expected_path)
        self.assertEqual(loaded_experiment, experiment)
        self.assertEqual(loaded_experiment.uuid, experiment.uuid)
        self.assertEqual(loaded_experiment.date_created, experiment.date_created)
        self.assertEqual(loaded_experiment.tree1, experiment.tree1)
        self.assertEqual(loaded_experiment.tree2, experiment.tree2)
        self.assertTrue(loaded_experiment._context, experiment._context)
        loaded_experiment._tree.close()

    def test_save_twice_experiment(self):
        """Test that an experiment is saved correctly twice, from the same instance."""
        expected_root_dir, user_root_dir = self.mkdtemp_root_dir_with_home(
            prefix="aardvark_test"
        )
        provider = FolderProvider()
        _context = provider.new_context()

        # *** 'save' an experiment
        experiment: MockExperiment = self.get_experiment(context=_context)
        config = get_config()
        expected_path = target_path_for(
            experiment=experiment,
            folder_format=config["storage_providers"]["folder_storage_provider"][
                "folder_format"
            ],
            filename_format=config["storage_providers"]["folder_storage_provider"][
                "filename_format"
            ],
            root_dir=str(expected_root_dir),
        )

        # Save experiment
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = user_root_dir
            self.assertEqual(
                get_config()["storage_providers"]["folder_storage_provider"][
                    "root_dir"
                ],
                user_root_dir,
                msg="Setting root_dir did not change value for get_config().",
            )
            experiment.save()

        _original_path = experiment._context._current_path

        # Save a second time
        experiment.tree2 = 2.718281828245901
        experiment.save()

        # Check context values
        self.assertEqual(
            experiment._context._current_path,
            expected_path,
            msg="Current path of FolderContext is not as expected.",
        )
        self.assertEqual(
            experiment._context._current_path,
            _original_path,
            msg="Current path of FolderContext changed during second save.",
        )
        self.assertEqual(
            experiment._context._state,
            ContextState.saved,
            msg="Saved experiment state must be ContextState.saved.",
        )
        self.assertTrue(expected_path.exists(), msg="Saved experiment does not exist.")

        # Check that saved experiment is correct.
        loaded_experiment = MockExperiment.load(expected_path)
        self.assertEqual(loaded_experiment, experiment)
        self.assertEqual(loaded_experiment.uuid, experiment.uuid)
        self.assertEqual(loaded_experiment.date_created, experiment.date_created)
        self.assertEqual(loaded_experiment.tree1, experiment.tree1)
        self.assertEqual(loaded_experiment.tree2, experiment.tree2)
        self.assertTrue(loaded_experiment._context, experiment._context)
        loaded_experiment._tree.close()

    def test_save_twice_asdffile(self):
        """Test that an asdffile is saved correctly twice using its builtin context."""
        expected_root_dir, user_root_dir = self.mkdtemp_root_dir_with_home(
            prefix="aardvark_test"
        )
        provider = FolderProvider()
        _context = provider.new_context()

        # *** 'save' an experiment
        experiment = self.get_experiment(context=_context)
        tree = experiment._tree
        context: FolderContext = experiment._context
        config = get_config()
        expected_path = target_path_for(
            experiment=tree,
            folder_format=config["storage_providers"]["folder_storage_provider"][
                "folder_format"
            ],
            filename_format=config["storage_providers"]["folder_storage_provider"][
                "filename_format"
            ],
            root_dir=str(expected_root_dir),
        )

        # Save experiment
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = user_root_dir
            context.save(experiment=tree)

        _path = context._current_path

        # Save a second time, with overwrite=True as the file already exists.
        tree["tree2"] = 2.71828182845901
        context.save(experiment=tree, overwrite=True)

        # Check context values
        self.assertEqual(
            context._current_path,
            expected_path,
            msg="Current path of FolderContext is not as expected.",
        )
        self.assertEqual(
            context._current_path,
            _path,
            msg="Current path of FolderContext changed since second save.",
        )
        self.assertEqual(
            experiment._context._state,
            ContextState.saved,
            msg="Saved experiment state must be ContextState.saved.",
        )
        self.assertTrue(expected_path.exists(), msg="Saved experiment does not exist.")

        # Check that saved experiment is correct.
        loaded_tree, loaded_context = FolderContext.load(expected_path)
        # We ignore the following tree keys as they are added by AsdfFile.write_to()
        ignored_asdf_keys = [
            "history",
            "asdf_library",
            # We ignore it in this test, but should be testing it somewhere
            # else.
            "artifacts",
        ]
        self.assertEqual(
            {k for k in loaded_tree.keys() if k not in ignored_asdf_keys},
            set(tree.keys()),
        )
        for k in tree.keys():
            self.assertEqual(
                loaded_tree[k],
                tree[k],
                msg="Loaded tree[{!r}] from context not as expected.".format(k),
            )
        self.assertEqual(loaded_tree["uuid"], tree["uuid"])
        self.assertEqual(loaded_tree["date_created"], tree["date_created"])
        self.assertEqual(loaded_tree["tree1"], tree["tree1"])
        self.assertEqual(loaded_tree["tree2"], tree["tree2"])
        self.assertEqual(context, loaded_context)
        loaded_tree.close()
        tree.close()
        experiment._tree.close()

    def test_artifact_save(self):
        """Test that floating artifacts are saved correctly."""
        expected_root_dir, user_root_dir = self.mkdtemp_root_dir_with_home(
            prefix="aardvark_test"
        )
        provider = FolderProvider()
        _context = provider.new_context()

        # *** 'save' an experiment
        exp = self.get_experiment(context=_context)
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = user_root_dir
            exp.save()

        log_str = "2025.01.01 00:00 This is a test\n"
        with exp.open_artifact("execution.log", "w", name="log") as f:
            f.write(log_str)
        with exp.open_artifact("execution.log", "r") as f:
            _read_str = f.read()
        self.assertEqual(
            _read_str,
            log_str,
            msg="Artifact read with open_artifact() has the wrong contents.",
        )
        with open(
            expected_root_dir.joinpath(exp._context._current_path.parent.name).joinpath(
                "execution.log"
            ),
            "r",
        ) as f:
            _read_str = f.read()
        self.assertEqual(
            _read_str,
            log_str,
            msg="Artifact read with open() has the wrong contents.",
        )

    @ddt.idata(
        [
            # "Normal" descriptions
            ("This is a description", "_This_is_a_desc", 15),
            ("This is a description", "_This_is", 9),
            ("This is a description", "_This_is_a", 11),
            ("This is a description", "_This_is_a_d", 12),
            # Lots of white space
            ("This      is      a      description", "_This_is_a_d", 12),
            # New lines
            ("This  \n  is\n\n      a      description", "_This_is_a_d", 12),
        ]
    )
    @ddt.unpack
    def test_description_truncate(
        self, input_desc: str, expected_desc: str, desc_max_length: int
    ):
        """Test that FolderContext descriptions are truncated correctly when computing folders and filenames."""
        actual_desc = transformed_description(input_desc, desc_max_length)
        self.assertTrue(
            len(actual_desc) <= desc_max_length,
            "Description is not truncated to within maximum length. Length is {} instead of <={}.".format(
                len(actual_desc), desc_max_length
            ),
        )
        self.assertEqual(
            actual_desc,
            expected_desc,
            "Formatted description is not correctly formatted for length {}.\nExpected '{}'\nActual '{}'".format(
                desc_max_length, expected_desc, actual_desc
            ),
        )

    def test_context_comparison(self):
        """Test that contexts compare correctly."""
        current_path = Path("/home/user/experiment/experiment.asdf")
        state = ContextState.saved
        artifacts = ArtifactCollection(
            [
                ArtifactInfo(
                    file="test.txt",
                    name="test",
                    description="This is a description.",
                    floating=True,
                ),
                ArtifactInfo(
                    file="execution.log",
                    name="execution",
                    description="This is a description.",
                    floating=True,
                ),
                ArtifactInfo(
                    file="figure1.pdf",
                    name="figure1",
                    description="This is a description.",
                    floating=True,
                ),
                ArtifactInfo(
                    file="results.npz",
                    name="results",
                    description="This is a description.",
                    format="npz",
                    floating=False,
                ),
            ]
        )
        context1 = FolderContext(
            current_path=current_path, state=state, artifacts=artifacts
        )
        context2 = FolderContext(
            current_path=current_path, state=state, artifacts=artifacts
        )
        self.assertEqual(
            context1,
            context2,
            msg="Contexts initialised in the same way should be equal.",
        )

        # Compare against different artifacts
        alt_artifacts = artifacts.artifacts()
        alt_artifacts.append(ArtifactInfo(file="alt.txt", name="alt", floating=True))
        context_alt_artifacts = FolderContext(
            current_path=current_path,
            state=state,
            artifacts=ArtifactCollection(alt_artifacts),
        )

        self.assertNotEqual(
            context1,
            context_alt_artifacts,
            msg="Contexts with different artifacts cannot be equal.",
        )

        # Compare against different paths
        context_alt_current_path = FolderContext(
            current_path=Path("/home/user/data/MyExp/MyExp.asdf"),
            state=state,
            artifacts=artifacts,
        )
        self.assertNotEqual(
            context1,
            context_alt_current_path,
            msg="Contexts with different paths cannot be equal.",
        )

        # Compare against different states
        context_alt_state = FolderContext(
            current_path=Path("/home/user/data/MyExp/MyExp.asdf"),
            state=ContextState.unsaved,
            artifacts=artifacts,
        )
        self.assertNotEqual(
            context1,
            context_alt_state,
            msg="Contexts with different states cannot be equal.",
        )


@ddt.ddt
class TestFolderContext_withPredefinedHome(TestFolderContext):

    _home: str

    def setUp(self) -> None:
        super().setUp()
        self._home = mkdtemp()
        self._previous_home = os.environ["HOME"]
        os.environ["HOME"] = self._home

    def tearDown(self) -> None:
        super().tearDown()
        os.environ["HOME"] = self._previous_home

    def test_expanduser_root_dir(self):
        """Test that we are correctly replacing HOME with a temporary folder."""
        _path = Path("~").expanduser()
        _expected_path = Path(self._home)
        self.assertEqual(
            _path,
            _expected_path,
            msg="pathlib.Path.expanduser() isn't correct, based on custom HOME env variable.",
        )
