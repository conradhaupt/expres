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

from io import BytesIO
from itertools import product
from os.path import join
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Literal as L
from unittest import mock

import asdf
import ddt
import numpy as np
from aardvark.artifacts import ArtifactCollection, ArtifactInfo
from aardvark.utils.tests import TestCase

# TODO: Copy over test utils from ASDF Qiskit.
from asdf_qiskit.tests.utils import roundtrip_object


@ddt.ddt
class TestArtifactsConverter(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.rng = np.random.default_rng(seed=314159)

    def random_source(
        self, source_type: L["posix", "windows"], prefix: str, i: int
    ) -> str:
        _posix_path = PurePosixPath(
            join(
                prefix,
                "{}.txt".format(i),
            )
        )
        if source_type == "posix":
            return str(_posix_path)
        else:
            return str(PureWindowsPath(_posix_path))

    def generated_artifacts(
        self, num_artifacts: int, source_type: L["posix", "windows"]
    ) -> ArtifactCollection:
        artifacts = ArtifactCollection()
        _prefix = ["data", "./data", "testing/../data"]
        for i in range(num_artifacts):
            _a = ArtifactInfo(
                file=self.random_source(
                    source_type=source_type,
                    prefix=str(self.rng.choice(_prefix, 1)[0]),
                    i=i,
                ),
                name="{}_{}.txt".format(
                    "".join(self.rng.choice(list("abcdefghijklmnopqrst"), (10,))), i
                ),
                description=(
                    "This is a test description." if self.rng.random() >= 0.5 else None
                ),
            )
            artifacts._add_artifact(artifact=_a)
        return artifacts

    @ddt.named_data(
        *[
            [
                "{} artifacts with {} paths".format(_num_artifacts, _source_type),
                _num_artifacts,
                _source_type,
            ]
            for _num_artifacts, _source_type in product(
                range(1, 6), ["posix", "windows"]
            )
        ]
    )
    def test_roundtrip(self, num_artifacts: int, source_type: L["posix", "windows"]):
        input_arts = self.generated_artifacts(
            num_artifacts=num_artifacts, source_type=source_type
        )
        output_arts: ArtifactCollection
        output_arts = roundtrip_object(input_arts)

        self.assertEqual(input_arts._artifacts.keys(), output_arts._artifacts.keys())
        self.assertEqual(
            input_arts._name_source_mapping.keys(),
            output_arts._name_source_mapping.keys(),
        )
        for _name in input_arts._name_source_mapping.keys():
            _in = input_arts[_name]
            _out = output_arts[_name]
            self.assertEqual(_in.name, _out.name)
            self.assertEqual(_in.source, _out.source)
            self.assertEqual(_in.description, _out.description)

    @ddt.named_data(
        *[
            [
                "{} artifacts".format(_num_artifacts),
                _num_artifacts,
            ]
            for _num_artifacts in range(1, 6)
        ]
    )
    def test_roundtrip_with_windows_path(self, num_artifacts: int):
        with mock.patch("aardvark.artifacts.artifact.InternalPath", PurePosixPath):
            input_posix_arts = self.generated_artifacts(
                num_artifacts=num_artifacts, source_type="posix"
            )

        output_windows_arts: ArtifactCollection
        # We copy code from roundtrip_object so we can mock the path used by ArtifactInfo.
        buff = BytesIO()
        with asdf.AsdfFile(version=None) as af:
            af["obj"] = input_posix_arts
            af.write_to(buff)

        buff.seek(0)
        # Mock the InternalPath class to emulate being on Windows
        with mock.patch("aardvark.artifacts.artifact.InternalPath", PureWindowsPath):
            with asdf.open(buff, lazy_load=False, memmap=False) as af:
                output_windows_arts = af["obj"]

        # We need to convert paths to compare them.
        self.assertEqual(
            {
                Path(PurePosixPath(_path))
                for _path in input_posix_arts._artifacts.keys()
            },
            {
                Path(PureWindowsPath(_path))
                for _path in output_windows_arts._artifacts.keys()
            },
        )
        self.assertEqual(
            input_posix_arts._name_source_mapping.keys(),
            output_windows_arts._name_source_mapping.keys(),
        )
        for _name in input_posix_arts._name_source_mapping.keys():
            _in_posix = input_posix_arts[_name]
            _out_windows = output_windows_arts[_name]
            self.assertEqual(
                _in_posix.name,
                _out_windows.name,
                "Name does not match for input artifact with name {!r} in roundtrip from POSIX path to Windows path.".format(
                    _name
                ),
            )
            self.assertEqual(
                _in_posix.source,
                str(PurePosixPath(PureWindowsPath(_out_windows.source))),
                "sources do not match when converted to POSIX path for artifact named {!r}.".format(
                    _name
                ),
            )
            self.assertEqual(
                str(PureWindowsPath(PurePosixPath(_in_posix.source))),
                _out_windows.source,
                "sources do not match when converted to Windows path for artifact named {!r}.".format(
                    _name
                ),
            )
            self.assertEqual(
                _in_posix.description,
                _out_windows.description,
                "Descriptions do not match for input artifact with name {!r} in roundtrip from POSIX path to Windows path.".format(
                    _name
                ),
            )
