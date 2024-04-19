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
from pathlib import Path
from typing import Literal

from aardvark.artifacts.typing import ArtifactFormat
from aardvark.utils.io import could_be_file_path
from aardvark.utils.io.typeshed import StrOrPath

from .paths import (
    file_to_path,
    path_to_source,
)

try:
    from typing import overload
except ImportError:
    from typing_extensions import overload


InternalPath = Path
"""Internal path type, allowing for Mock testing."""


class ArtifactInfo:
    """Custom class representing an artifact.

    Artifacts have a name, a path to the artifact source file, and an optional
    description. If no name is provided, ``name`` in :meth:`__init__`, then
    ``file`` is used as the name. ``file`` is processed and used as the
    ``source`` value. ``file`` is converted into a string on construction.

    Note that all paths in ``source`` are POSIX paths. If you are on Windows and
    create an Artifact with a Windows path, it will be converted. It is
    undefined behaviour to pass a Windows path as a string or bytes literal on a
    non-Windows platform. Instead, pass a :class:`pathlib.PureWindowsPath`
    instance to ``file``.
    """

    @overload
    def __init__(
        self,
        file: StrOrPath,
        name: str = ...,
        description: str | None = ...,
        format: ArtifactFormat = ...,
        floating: Literal[False] = ...,
    ): ...
    @overload
    def __init__(
        self,
        file: StrOrPath,
        name: str | None = ...,
        description: str | None = ...,
        format: None = ...,
        floating: Literal[True] = ...,
    ): ...
    def __init__(
        self,
        file: StrOrPath,
        name: str | None = None,
        description: str | None = None,
        format: ArtifactFormat | None = None,
        floating: bool = True,
    ):
        """Create an artifact for the given file.

        Args:
            file: Relative path to the file. String literals must be in the
                format of the current platform. Any :class:`~pathlib.PurePath`
                subclass is allowed. Note that paths are converted to POSIX
                paths when serialised.
            name: Name of the artifact. If ``floating=False``, this is the name
                of the attribute bound to this artifact. If ``floating=True``
                and ``name`` is None, then ``name=file``. Defaults to None.
            description: Optional description for the artifact, which is stored
                in the final ASDF file. Defaults to None.
            format: Format of the artifact. This is used to determine how to
                serialise and deserialise bound artifacts. If ``floating=True``,
                then ``format`` must be None. If ``floating=False``, then
                ``format`` cannot be None. Defaults to None.
            floating: If this refers to a floating artifact. If False, this is a
                bound artifact, bound to an attribute called ``name``.

        Raises:
            ValueError: If creating a bound artifact, i.e., ``floating=False``,
                but ``name`` is not provided.
            ValueError: If ``floating=False`` and ``name`` is not a valid Python
                attribute name.
            ValueError: If creating a bound artifact, i.e., ``floating=False``,
                but ``format`` is not provided.
            ValueError: If ``file`` refers to a relative file, such as a path
                ending in a directory separator.
        """
        # Check if we're creating a bound artifact and we have name.
        if not floating:
            if name is None:
                raise ValueError("Cannot create a bound artifact without a name.")
            else:
                # Check that name, which is the attribute to which this artifact is
                # bound, is a valid Python attribute name.
                _match = re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name)
                if _match is None:
                    raise ValueError(
                        "Artifact name {!r}, for a bound artifact, must be a valid Python attribute name.".format(
                            name
                        )
                    )

            if format is None:
                raise ValueError("Cannot create a bound artifact without a format.")
            else:
                if not self._is_valid_format(format):
                    raise ValueError(
                        "Unrecognised bound artifact format {!r}.".format(format)
                    )

        # Validate string paths to confirm they're not referring to a folder. We
        # cannot do this for paths without the path existing, so we don't check.
        if isinstance(file, str):
            if not could_be_file_path(file):
                raise ValueError("file cannot be a path to a directory.")
        # Convert all versions of file to the system-native path object from Pathlib.
        file = file_to_path(file)

        # Save the path in the current platform format.
        self._file = InternalPath(file)
        if self._file.is_absolute():
            raise ValueError("file must be a relative path.")

        self._name = name
        self._description = description
        self._floating = floating
        self._format: ArtifactFormat | None = format

    def _is_valid_format(self, format: ArtifactFormat) -> bool:
        return format in ["npz"]

    def is_floating(self) -> bool:
        """If this artifact is floating."""
        return self._floating

    def is_bound(self) -> bool:
        """If this artifact is floating."""
        return not self._floating

    @property
    def attr(self) -> str:
        """The attribute name bound to this artifact if it is not floating."""
        if self.is_floating():
            raise ValueError("A floating artifact does not have an attribute.")
        return self.name

    @property
    def name(self) -> str:
        """The name of the artifact.

        For floating artifacts, this is the name of the artifact. If ``name``
        was not provided on construction, this is the filename from ``file``.
        For bound artifacts, this is the name of the Python attribute in an
        experiment to which this artifact is bound.
        """
        if self._name is None:
            return self._file.name
        else:
            return self._name

    @property
    def source(self) -> str:
        """The path to the artifact source file.

        Should be a relative path to a file. Note that the path will be
        converted to a POSIX path when serialised. The POSIX path is converted
        to the current platform's path when loading an ASDF file.
        """
        return path_to_source(self._file)

    @property
    def format(self) -> ArtifactFormat | None:
        return self._format

    @property
    def description(self) -> str | None:
        return self._description

    @description.setter
    def description(self, desc: str | None):
        self._description = desc

    def __eq__(self, value: object, /) -> bool:
        return all(
            getattr(value, attr) == getattr(self, attr)
            for attr in ["_file", "_name", "_description"]
        )

    def __neq__(self, value: object, /) -> bool:
        return any(
            getattr(value, attr) != getattr(self, attr)
            for attr in ["_file", "_name", "_description"]
        )

    def __hash__(self) -> int:
        return hash(
            tuple(getattr(self, attr) for attr in ["_file", "_name", "_description"])
        )

    def __repr__(self) -> str:
        if self.description is None:
            return "{}(name={!r}, source={!r})".format(
                self.__class__.__name__, self.name, self.source
            )
        else:
            return "{}(name={!r}, source={!r}, desc={!r}{})".format(
                self.__class__.__name__,
                self.name,
                self.source,
                self.description[:30],
                "..." if len(self.description) > 30 else "",
            )
