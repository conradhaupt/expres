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

from copy import deepcopy as copy

from aardvark.utils.containers import update_nested_dictionaries
from aardvark.utils.tests import TestCase


class TestUpdateNestedDictionaries(TestCase):
    def test_update_nested_dictionaries(self):
        # We use an example config file to test, because it is clearer to read.
        dict1 = {
            "current_version": "0.1.0",
            "storage_providers": {
                "folder_storage_provider": {
                    "root_dir": "/home/user/data/",
                    "folder_format": "{uuid_short}",
                    "filename_format": "{uuid_short}.asdf",
                },
                "remote_provider": {
                    "root_dir": "ssh://user@dataserver.internal.com:/home/user/data/",
                    "folder_format": "{uuid_short}",
                    "filename_format": "{uuid_short}.asdf",
                },
            },
        }

        # This models updating a dictionary with a new
        # storage_providers.folder_storage_provider.root_dir value, only.
        dict2 = {
            "storage_providers": {
                "folder_storage_provider": {"root_dir": "/home/user2/data_backup"}
            }
        }

        expected = {
            "current_version": "0.1.0",
            "storage_providers": {
                "folder_storage_provider": {
                    # *** This is the only key that should be different
                    "root_dir": dict2["storage_providers"]["folder_storage_provider"][
                        "root_dir"
                    ],
                    # ***
                    "folder_format": "{uuid_short}",
                    "filename_format": "{uuid_short}.asdf",
                },
                "remote_provider": {
                    "root_dir": "ssh://user@dataserver.internal.com:/home/user/data/",
                    "folder_format": "{uuid_short}",
                    "filename_format": "{uuid_short}.asdf",
                },
            },
        }

        actual = copy(dict1)
        update_nested_dictionaries(actual, dict2)
        self.assertEqual(expected, actual)
