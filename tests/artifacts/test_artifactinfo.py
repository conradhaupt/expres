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

from itertools import product
from os.path import join as path_join
from pathlib import Path, PurePosixPath, PureWindowsPath

import ddt
from aardvark.artifacts import ArtifactInfo
from aardvark.utils.tests import TestCase

VALID_ARTIFACT_PATHS_POSIX = [
    # Linux and MacOS paths
    "test.json",
    "./test.json",
    "data/test.json",
    "./data/test.json",
]
VALID_ARTIFACT_PATHS_WINDOWS = [
    # Windows paths
    "test.json",
    ".\\test.json",
    "data\\test.json",
    ".\\data\\test.json",
]
VALID_ARTIFACT_PATHS_POSIX_WINDOWS_PAIRED = list(
    zip(VALID_ARTIFACT_PATHS_POSIX, VALID_ARTIFACT_PATHS_WINDOWS)
)
VALID_ARTIFACT_PATHS = VALID_ARTIFACT_PATHS_POSIX + VALID_ARTIFACT_PATHS_WINDOWS

INVALID_ARTIFACT_PATHS = [
    # Linux and MacOS paths
    ".",
    "..",
    "data/",
    "./data/",
    "/home/user/data/",
    "data/.",
    "data/..",
    "./data/.",
    "./data/..",
    "/home/user/data/.",
    "/home/user/data/..",
    # Windows paths
    "data\\",
    ".\\data\\",
    "C:\\Users\\user\\data\\",
    "data\\.",
    "data\\..",
    ".\\data\\.",
    ".\\data\\..",
    "C:\\Users\\user\\data\\.",
    "C:\\Users\\user\\data\\..",
]


@ddt.ddt
class TestArtifactInfo(TestCase):
    @ddt.idata(VALID_ARTIFACT_PATHS)
    def test_artifacts_with_name(self, file: str):
        _name = "this is a name"
        _path = Path(file)
        artifact = ArtifactInfo(file=file, name=_name)
        self.assertEqual(artifact.source, str(_path))
        self.assertEqual(artifact.name, _name)
        self.assertIsNone(artifact.description)

    @ddt.idata(VALID_ARTIFACT_PATHS)
    def test_artifacts_without_name(self, file: str):
        artifact = ArtifactInfo(file=file)
        _path = Path(file)
        self.assertEqual(artifact.source, str(_path))
        self.assertEqual(artifact.name, _path.name)
        self.assertIsNone(artifact.description)

    @ddt.idata(
        [
            (path_join(path, file), name)
            for path, (file, name) in product(
                VALID_ARTIFACT_PATHS, [("a.txt", "a.txt")]
            )
        ]
    )
    @ddt.unpack
    def test_artifact_correctly_deduces_name_from_source(
        self, file: str, expected_name: str
    ):
        artifact = ArtifactInfo(file=file)
        self.assertEqual(
            artifact.name,
            expected_name,
            "Actual deduced name is not as expected: expected {!r} but got {!r}.".format(
                expected_name, artifact.name
            ),
        )

    def test_artifacts_with_description(self):
        file = "test.json"
        description = "This is a description"
        _path = Path(file)
        artifact = ArtifactInfo(file=file, description=description)
        self.assertEqual(artifact.source, str(_path))
        self.assertEqual(artifact.name, _path.name)
        self.assertEqual(artifact.description, description)

        new_description = "This is a new description."
        artifact.description = new_description
        self.assertEqual(
            artifact.source,
            str(_path),
            msg="Modifying description should not modify source.",
        )
        self.assertEqual(
            artifact.name,
            _path.name,
            msg="Modifying description should not modify name.",
        )
        self.assertEqual(artifact.description, new_description)

    @ddt.idata(INVALID_ARTIFACT_PATHS)
    def test_fails_invalid_source(self, file: str):
        with self.assertRaises(ValueError):
            ArtifactInfo(file)

    @ddt.idata(VALID_ARTIFACT_PATHS_POSIX_WINDOWS_PAIRED)
    @ddt.unpack
    def test_posix_windows_equality(self, posix_file: str, windows_file: str):
        windows_path = PureWindowsPath(windows_file)
        posix_path = PurePosixPath(posix_file)
        windows_artifact = ArtifactInfo(file=windows_path, name="myfile")
        posix_artifact = ArtifactInfo(file=posix_path, name="myfile")
        self.assertEqual(
            windows_artifact,
            posix_artifact,
            msg="Artifacts equality should be invariant to path platform: windows vs posix.",
        )
