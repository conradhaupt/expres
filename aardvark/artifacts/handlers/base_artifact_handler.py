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

import abc
from pathlib import Path
from typing import Any

from aardvark.artifacts.typing import ArtifactFormat


class BaseArtifactHandler(abc.ABC):
    """Handler for saving and loading bound artifacts."""

    @property
    @abc.abstractmethod
    def format(self) -> ArtifactFormat:
        """Returns the artifact format supported by this handler."""
        ...

    @classmethod
    @abc.abstractmethod
    def source_for(cls, attr: str) -> str:
        """Compute the source for an artifact of this format bound to an
        attribute called ``attr``.

        This is the default source string, which can be overridden in
        :fun:`~aardvark.dataclasses.artifact`.

        Args:
            attr: The name of the attribute to which this artifact is bound.

        Returns:
            The source fileattr for this artifact bound to an attribute called
            ``attr``.
        """
        ...

    @abc.abstractmethod
    def save_obj_to(self, obj: Any, path: Path):
        """Save an object to a file at ``path``.

        Args:
            obj: Object compatible with :attr:`format`.
            path: The :class:`pathlib.Path` to the file to which the object
            should be saved.
        """
        ...

    @abc.abstractmethod
    def load_obj_from(self, path: Path) -> Any:
        """Load an object from ``path``.

        The file at ``path`` must be compatible with :attr:`format`.

        Args:
            path: Path to the file to be opened and from which the object should
                be loaded.

        Returns:
            The object stored in the file at ``path``.
        """
        ...
