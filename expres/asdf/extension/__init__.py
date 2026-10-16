# This code is part of Exprés.
#
# Copyright 2024-2026 Conrad Haupt <conrad@conradhaupt.com> and IBM.
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

from asdf.extension import Extension, ManifestExtension

from expres.asdf.converters.artifacts_converter import ArtifactConverter
from expres.asdf.converters.uuid import UUIDConverter


class ExpresExtension(ManifestExtension):
    """Custom ASDF extension to override yaml_tag_handles."""

    @property
    def yaml_tag_handles(self):
        return {
            # For old Aardvark tags
            "!aardvark!": "asdf://aardvark.org/asdf/tags/",
            # For first-class Aardvark tags
            "!expres!": "asdf://expres.org/asdf/tags/",
            # For legacy tags moved from ASDF Qiskit to Aardvark
            "!qiskit!": "asdf://qiskit.org/asdf/tags/",
        }


def get_extensions() -> list["Extension"]:
    converters = [ArtifactConverter(), UUIDConverter()]
    return [
        ExpresExtension.from_uri(
            "asdf://expres.org/asdf/manifests/expres-0.2.0",
            converters=converters,
        ),
        ExpresExtension.from_uri(
            "asdf://aardvark.org/asdf/manifests/aardvark-0.0.0",
            converters=converters,
        ),
    ]
