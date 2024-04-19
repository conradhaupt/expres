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

from aardvark.artifacts.artifact import ArtifactInfo
from aardvark.artifacts.typing import ArtifactFormat
from aardvark.dataclasses import dataclass, field


@dataclass
class ArtifactInfoTag:
    """Tag class for storing ASDF ArtifactInfo information.

    This is used as temporary storage during serialisation and deserialisation
    of artifacts. This defers checks made by :class:`ArtifactInfo` to
    :meth:`to_artifact_info`.
    """

    source: str
    floating: bool
    name: str | None = field(default=None)
    description: str | None = field(default=None)
    format: ArtifactFormat | None = field(default=None)

    def to_artifact_info(self, name: str | None = None) -> ArtifactInfo:
        """Create an :class:`ArtifactInfo` instance for this Tag.

        Args:
            name: Optional name. Required if :attr:`name` is None. If None,
                :attr:`name` is used as the name of the returned
                :class:`ArtifactInfo` instance. Defaults to None.

        Returns:
            An instance of :class:`ArtifactInfo` with the same data as is in
            this instance of :class:`ArtifactInfoTag`.

        Raises:
            Any exception raised by :class:`ArtifactInfo` upon creation, if the
            attributes have incorrect values.
        """
        # We don't do any checking here as we delegate that to ArtifactInfo.
        return ArtifactInfo(  # pyright: ignore[reportCallIssue]
            file=self.source,
            name=name if name is not None else self.name,
            description=self.description,
            format=self.format,
            floating=self.floating,
        )
