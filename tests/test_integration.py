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

import re
import tempfile
from pathlib import Path

import numpy as np
import numpy.typing as npt
import yaml
from aardvark.storage.base_provider import ContextState
from aardvark.utils.tests import TestCase


# Create a Loader for unknown YAML types so we don't need to worry about ASDF
# tags in YAML. This treats unknown tags as if they didn't exist, but still
# parses their values as normal YAML types.
class DummyLoader(yaml.FullLoader):
    pass


def unknown(loader, node):
    if isinstance(node, yaml.ScalarNode):
        constructor = loader.__class__.construct_scalar
    elif isinstance(node, yaml.SequenceNode):
        constructor = loader.__class__.construct_sequence
    elif isinstance(node, yaml.MappingNode):
        constructor = loader.__class__.construct_mapping

    data = constructor(loader, node)

    return data


DummyLoader.add_constructor(None, unknown)


class TestIntegration(TestCase):
    def test_save_load_simple_class(self):
        from aardvark import Experiment, dataclass, field, temp_config

        @dataclass
        class MyExp(Experiment):
            x: list[int]
            y: list[int]
            z: list[int] | None = field(default=None)

        expected_x = [0, 1, 2, 3]
        expected_y = [4, 5, 6, 7]
        expected_z = [9, 8, 7, 6]
        with temp_config() as _config:
            _root_dir = tempfile.gettempdir()
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = _root_dir

            inst = MyExp(x=expected_x, y=expected_y)
            inst.z = expected_z
            inst.save()
            _target_path = inst._context._current_path

        self.assertTrue(Path(_target_path).exists())

        with open(inst._context._current_path, "rb") as f:
            _data = f.read()
            self.assertTrue(
                bytes(str(inst.z), encoding="utf-8") in _data,
                "ASDF file does not contain known attributes.",
            )

        # Test that we can save again.
        new_z = [0, 1, 2, 3]
        with temp_config() as _config:
            inst.z = new_z
            inst.save()
        self.assertEqual(
            _target_path,
            inst._context._current_path,
            msg="Instance path changed after saving again.",
        )
        with open(inst._context._current_path, "rb") as f:
            _data = f.read()
            self.assertTrue(
                bytes(str(inst.z), encoding="utf-8") in _data,
                "ASDF file does not contain modified known attributes.",
            )

    def test_load_and_save_experiment(self):
        from aardvark import Experiment, dataclass, field, temp_config

        @dataclass
        class MyExp(Experiment):
            x: list[int]
            y: list[int]
            z: list[int] | None = field(default=None)

        expected_x = [0, 1, 2, 3]
        expected_y = [4, 5, 6, 7]
        expected_z = [9, 8, 7, 6]

        def _save() -> Path:
            with temp_config() as _config:
                _root_dir = tempfile.gettempdir()
                _config["storage_providers"]["folder_storage_provider"][
                    "root_dir"
                ] = _root_dir

                inst = MyExp(x=expected_x, y=expected_y)
                inst.z = expected_z
                inst.save()

            _path = Path(inst._context._current_path)
            self.assertTrue(_path.exists())
            return _path

        _path = _save()

        # Test that we can load and then save
        new_new_z = [-1, -2, -3, -4]
        new_inst = MyExp.load(_path)
        self.assertEqual(
            new_inst._context._current_path,
            _path,
            msg="Loaded instance has different path to original.",
        )
        self.assertEqual(
            new_inst._context._state,
            ContextState.saved,
            msg="Loaded instance has incorrect state.",
        )
        new_inst.z = new_new_z
        new_inst.save()
        self.assertEqual(
            new_inst._context._current_path,
            _path,
            msg="Loaded instance has different path after saving.",
        )

        with open(_path, "rb") as f:
            _data = f.read()
            self.assertTrue(
                bytes(str(new_inst.z), encoding="utf-8") in _data,
                "ASDF file for loaded instance does not contain modified known attributes.",
            )
        new_inst._tree.close()

    def test_save_numpy_class(self):
        from aardvark import Experiment, dataclass, field, temp_config

        @dataclass
        class MyExp(Experiment):
            x: list[int]
            y: list[int]
            z: list[int] | None = field(default=None)
            w: npt.NDArray[np.float64] | None = field(default=None)

        with temp_config() as _config:
            _root_dir = tempfile.gettempdir()
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = _root_dir

            inst = MyExp(x=[0, 1, 2, 3], y=[4, 5, 6, 7])
            inst.z = [9, 8, 7, 6]
            inst.w = np.arange(10)
            inst.save()
            _target_path = inst._context._current_path

        self.assertTrue(Path(_target_path).exists())

        # Check that we saved a numpy array by verifying we refer to a binary
        # block as source, somewhere. The source should be block 0 and the shape
        # is [10].
        with open(inst._context._current_path, "rb") as f:
            _data = f.read()
            idx = _data.find(bytes("...", encoding="utf-8"))
            _data = _data[:idx].decode("utf-8")

        _match = re.search("source: 0", _data)
        self.assertIsNotNone(
            _match,
            msg="Cannot confirm numpy array for attribute was saved correctly, based on source.",
        )
        _match = re.search("shape: \\[10\\]", _data)
        self.assertIsNotNone(
            _match,
            msg="Cannot confirm numpy array for attribute was saved correctly, based on shape.",
        )

        with temp_config() as _config:
            _root_dir = tempfile.gettempdir()
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = _root_dir

            inst.w = np.arange(100)
            inst.save()

        # Check that we saved a numpy array by verifying we refer to a binary
        # block as source, somewhere. The source should not have changed, but
        # the shape would have.
        with open(inst._context._current_path, "rb") as f:
            _data = f.read()
            idx = _data.find(bytes("...", encoding="utf-8"))
            _data = _data[:idx].decode("utf-8")

        _match = re.search("source: 0", _data)
        self.assertIsNotNone(
            _match,
            msg="Cannot confirm numpy array for attribute was saved correctly, based on source.",
        )
        _match = re.search("shape: \\[100\\]", _data)
        self.assertIsNotNone(
            _match,
            msg="Cannot confirm numpy array for attribute was saved correctly, based on shape.",
        )

    def test_save_floating_artifact(self):
        from aardvark import Experiment, dataclass, field, temp_config

        @dataclass
        class MyExp(Experiment):
            x: list[int]
            y: list[int]
            z: list[int] | None = field(default=None)
            w: npt.NDArray[np.float64] | None = field(default=None)

        inst = MyExp(x=[0, 1, 2, 3], y=[4, 5, 6, 7])
        inst.z = [9, 8, 7, 6]
        inst.w = np.arange(10)

        with temp_config() as _config:
            _root_dir = tempfile.gettempdir()
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = _root_dir

            inst.save()

        with inst.open_artifact("test.txt", "w", "test") as f:
            f.write("This is a test.")

        _target_path = inst._context._current_path

        self.assertTrue(Path(_target_path).exists())
        self.assertTrue(Path(_target_path).parent.joinpath(Path("test.txt")).exists())

        with open(inst._context._current_path, "rb") as f:
            _data = f.read()
            idx = _data.find("...".encode("utf-8"))
            _data = _data[:idx].decode("utf-8")

            tree = yaml.load(_data, Loader=DummyLoader)
        self.assertTrue(
            "test" in tree["artifacts"], msg="Floating artifact 'test' does not exist."
        )
        self.assertEqual(
            tree["artifacts"]["test"]["source"],
            "test.txt",
            msg="Floating artifact source is incorrect.",
        )
        self.assertIsNone(
            tree["artifacts"]["test"].get("description", None),
            msg="Floating artifact description is incorrect.",
        )
        with open(
            inst._context._current_path.parent.joinpath(
                tree["artifacts"]["test"]["source"]
            ),
            "r",
        ) as f:
            _artifact_test = f.read()
            self.assertEqual(
                _artifact_test,
                "This is a test.",
                msg="Floating artifact contents is incorrect.",
            )

    def test_save_bound_artifact(self):
        from aardvark import Experiment, artifact, dataclass, field, temp_config

        @dataclass
        class MyExp(Experiment):
            x: list[int]
            y: list[int]
            z: list[int] | None = field(default=None)
            w: npt.NDArray[np.float64] | None = artifact(format="npz", default=None)

        inst = MyExp(x=[0, 1, 2, 3], y=[4, 5, 6, 7])
        inst.z = [9, 8, 7, 6]
        inst.w = np.arange(10)

        self.assertEqual(
            len(inst._context.artifacts.bound_artifacts()),
            1,
            msg="Number of bound artifacts not as expected.",
        )
        self.assertEqual(
            inst._context.artifacts.bound_artifacts()[0].attr,
            "w",
            msg="Bound artifact attr not as expected.",
        )
        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = tempfile.gettempdir()

            inst.save()

        _target_path = inst._context._current_path

        self.assertTrue(
            Path(_target_path).exists(), msg="Saved ASDF file does not exist."
        )
        self.assertTrue(
            Path(_target_path).parent.joinpath(Path("w.npz")).exists(),
            "Saved bound artifact not found.",
        )

    def test_save_floating_and_bound_artifacts(self):
        from aardvark import Experiment, artifact, dataclass, field, temp_config

        @dataclass
        class MyExp(Experiment):
            x: list[int]
            y: list[int]
            z: list[int] | None = field(default=None)
            w: npt.NDArray[np.float64] | None = artifact(format="npz", default=None)

        inst = MyExp(x=[0, 1, 2, 3], y=[4, 5, 6, 7])
        inst.z = [9, 8, 7, 6]
        inst.w = np.arange(10)

        self.assertEqual(
            len(inst._context.artifacts.bound_artifacts()),
            1,
            msg="Number of bound artifacts not as expected.",
        )
        self.assertEqual(
            inst._context.artifacts.bound_artifacts()[0].attr,
            "w",
            msg="Bound artifact attr not as expected.",
        )

        with inst.open_artifact("test.txt", "w") as f:
            f.write("This is a test.")

        with temp_config() as _config:
            _config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = tempfile.gettempdir()

            inst.save()

        _target_path = inst._context._current_path

        self.assertTrue(_target_path.exists(), msg="Saved ASDF file does not exist.")
        self.assertTrue(
            _target_path.parent.joinpath(Path("w.npz")).exists(),
            "Saved bound artifact not found.",
        )
        self.assertTrue(
            _target_path.parent.joinpath(Path("test.txt")).exists(),
            "Saved bound artifact not found.",
        )
        with open(_target_path.parent.joinpath(Path("test.txt"))) as f:
            self.assertEqual(
                "This is a test.",
                f.read(),
                msg="Contents of floating artifact is incorrect.",
            )
