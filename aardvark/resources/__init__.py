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

# integration.py
from pathlib import Path

from asdf.resource import DirectoryResourceMapping


def get_resource_mappings():
    # Get path to schemas directory relative to this file
    root_path = Path(__file__).parent
    schemas_path = root_path.joinpath("schemas")
    manifests_path = root_path.joinpath("manifests")
    schema_mapping = DirectoryResourceMapping(
        schemas_path,
        "asdf://aardvark.org/asdf/schemas/",
        recursive=True,
        filename_pattern="*.yaml",
        stem_filename=True,
    )
    manifests_mapping = DirectoryResourceMapping(
        manifests_path,
        "asdf://aardvark.org/asdf/manifests/",
        recursive=True,
        filename_pattern="*.yaml",
        stem_filename=True,
    )
    return [
        schema_mapping,
        manifests_mapping,
    ]
