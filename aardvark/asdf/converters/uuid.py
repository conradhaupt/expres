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

from os.path import join
from uuid import UUID

from asdf.extension import Converter


class UUIDConverter(Converter):
    """Converter for :class:`~uuid.UUID` instances.

    Though UUIDs come in multiple formats, such as :meth:`uuid.uuid4`, they are
    all stored as a sequence of bits in :class:`UUID` instances.
    :class:`UUIDConverter` stores them in YAML with their hexadecimal value:
    ``_uuid.hex``.
    """

    tags = ["asdf://qiskit.org/asdf/tags/core/uuid-0.0.0"]
    """YAML tags for UUID types."""
    types = ["uuid.UUID", UUID]
    """Types that are serialisable by :class:`UUIDConverter`."""

    def to_yaml_tree(self, obj: UUID, tag, ctx):
        return obj.hex

    def from_yaml_tree(self, node: str, tag, ctx):
        return UUID(node)
