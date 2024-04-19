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

import aardvark.utils.io as io_utils
import ddt
from aardvark.utils.tests import TestCase


@ddt.ddt
class TestIOUtils(TestCase):
    @ddt.idata(
        [
            (x,)
            for x in [
                # Linux paths
                "test.json",
                "./test.json",
                "data/test.json",
                "./data/test.json",
                "/home/user/test.json",
                # Windows paths
                ".\\test.json",
                "data\\test.json",
                ".\\data\\test.json",
                "C:\\Users\\user\\test.json",
                # MacOS Paths
                "/Users/user/test.json",
            ]
        ]
    )
    @ddt.unpack
    def test_valid_paths(self, path: str):
        self.assertTrue(
            io_utils.could_be_file_path(path),
            msg="{} could be a valid file path, but `could_be_file_path` is False.".format(
                path
            ),
        )

    @ddt.idata(
        [
            (x,)
            for x in [
                # Linux paths
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
        ]
    )
    @ddt.unpack
    def test_invalid_paths(self, path: str):
        self.assertFalse(
            io_utils.could_be_file_path(path),
            msg="{} cannot be a valid file path, but `could_be_file_path` is True.".format(
                path
            ),
        )
