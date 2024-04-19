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

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from io import BufferedRandom, BufferedReader, BufferedWriter, FileIO, TextIOWrapper
import os
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Literal,
    NoReturn,
    overload,
)

from asdf import AsdfFile
from matplotlib import rcParams
from matplotlib.figure import Figure

from aardvark.artifacts import ArtifactCollection, ArtifactInfo, file_to_source
from aardvark.utils.io.typeshed import (
    OpenBinaryMode,
    OpenBinaryModeReading,
    OpenBinaryModeUpdating,
    OpenBinaryModeWriting,
    OpenTextMode,
    StrOrPath,
    _Opener,
)

try:
    from typing import Self
except:
    from typing_extensions import Self

if TYPE_CHECKING:
    from aardvark import Experiment


class ContextState(Enum):
    unsaved = 0
    """The context is stored in a temporary directory."""
    staging = 1
    """The context is currently being saved to the target directory."""
    saved = 2
    """The context is stored in the target directory."""


def source_to_figure_format(source: str) -> str | None:
    """Determine the format of a figure based on its source string.

    Args:
        source: The source of the figure artifact.

    Returns:
        The format of the figure, or None if it could not be determined.
    """
    format = os.path.splitext(source)[1][1:]
    if format == "":
        return None
    return format


class BaseProvider(ABC):
    @abstractmethod
    def new_context(self) -> BaseContext: ...


class BaseContext(ABC):
    _state: ContextState
    artifacts: ArtifactCollection

    def __new__(cls, /, **kwargs) -> Self:
        """Create a new instance of :class:`BaseContext`.

        Args:
            state: Override the initial state of the context. Defaults to :attr:`ContextState.unsaved`.

        """
        inst = super().__new__(cls)
        inst._state = kwargs.pop("state", ContextState.unsaved)
        inst.artifacts = ArtifactCollection()
        return inst

    @property
    def state(self) -> ContextState:
        return self._state

    @classmethod
    @abstractmethod
    def load(cls, file: StrOrPath) -> tuple[AsdfFile, Self]:
        """Load an experiment from ``file``.

        Args:
            file: The path to the asdf file to be loaded.

        Returns:
            The loaded ASDF file and its associated context.
        """
        ...

    @abstractmethod
    def save(
        self,
        experiment: "Experiment | AsdfFile",
        overwrite: bool = False,
        asdf_write_to_kwargs: dict[str, Any] = {},
    ):
        """Save an experiment instance.

        Args:
            experiment: The experiment to save or the associated ASDF file.
            overwrite: Whether to overwrite any existing saved experiment, if
                they have the same ``uuid``, ``date_created``, and subclass.
                Defaults to False.
            asdf_write_to_kwargs: Optional kwargs to pass to
                :meth:`asdf.AsdfFile.write_to`. Defaults to {}.
        """
        ...

    @overload
    def register_artifact(
        self,
        file: StrOrPath,
        name: str | None,
        description: str | None,
        artifact_info: None,
    ): ...
    @overload
    def register_artifact(
        self,
        file: None,
        name: None,
        description: None,
        artifact_info: ArtifactInfo,
    ): ...
    def register_artifact(
        self,
        file: StrOrPath | None = None,
        name: str | None = None,
        description: str | None = None,
        artifact_info: ArtifactInfo | None = None,
    ):
        """Add a floating artifact.

        Args:
            file: The filename or relative path to the artifact. If None,
                ``artifact_info`` must be provided. Defaults to None.
            name: Optional name for the artifact. Requires ``file``. If None,
                the basename of ``file`` is used. Defaults to None.
            description: Optional description of the artifact, only included in
                the ASDF file. Requires ``file``. Defaults to None.
            artifact_info: An instance of ArtifactInfo, identifying the
                artifact. If None, ``file`` must be provided. Defaults to None.
        """
        if artifact_info is not None and artifact_info.is_bound():
            raise NotImplementedError(
                "Cannot register a bound artifact during runtime."
            )
        self.artifacts._add_artifact(
            file=file, name=name, description=description, artifact=artifact_info
        )

    @overload
    def deregister_artifact(
        self,
        file: StrOrPath,
        name: str | None,
        artifact_info: None,
    ) -> None: ...
    @overload
    def deregister_artifact(
        self,
        file: None,
        name: None,
        artifact_info: ArtifactInfo,
    ) -> None: ...
    def deregister_artifact(
        self,
        file: StrOrPath | None = None,
        name: str | None = None,
        artifact_info: ArtifactInfo | None = None,
    ) -> None | NoReturn:
        """Remove a floating artifact identified by the given ``file`` and ``name``.

        Args:
            file: Optional filename or relative path to the artifact. If
                provided, ``artifact_info`` must be None. Defaults to None.
            name: Optional name of the artifact. If provided, ``artifact_info``
                must be None. Defaults to None.
            artifact_info: Optional :class:`ArtifactInfo`. If provided, ``file``
                and ``name`` must both be None. Defaults to None.

        Raises:
            ValueError: If the artifact is not found.
        """
        if file is not None:
            source = file_to_source(file)
        if artifact_info is not None and artifact_info.is_bound():
            raise NotImplementedError("Cannot deregister a bound artifact.")
        self.artifacts._remove_artifact(
            name=name, source=source, artifact=artifact_info
        )

    # Text mode: always returns a TextIOWrapper
    @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: OpenTextMode = "r",
        name: str | None = None,
        description: str | None = None,
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> TextIOWrapper: ...

    # Unbuffered binary mode: returns a FileIO
    @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: OpenBinaryMode = ...,
        name: str | None = None,
        description: str | None = None,
        buffering: Literal[0] = ...,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> FileIO: ...

    # Buffering is on: return BufferedRandom, BufferedReader, or BufferedWriter
    @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: OpenBinaryModeUpdating = ...,
        name: str | None = None,
        description: str | None = None,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> BufferedRandom: ...
    @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: OpenBinaryModeWriting = ...,
        name: str | None = None,
        description: str | None = None,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> BufferedWriter: ...
    @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: OpenBinaryModeReading = ...,
        name: str | None = None,
        description: str | None = None,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> BufferedReader: ...

    # Buffering cannot be determined: fall back to BinaryIO
    @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: OpenBinaryMode = ...,
        name: str | None = None,
        description: str | None = None,
        buffering: int = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> BinaryIO: ...

    # Fallback if mode is not specified
    # @overload
    @abstractmethod
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: str = "r",
        name: str | None = None,
        description: str | None = None,
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> IO[Any]:
        """Open an artifact as a Python file, saving as a floating artifact if necessary.

        If the artifact was never opened, a new file is created. New artifacts
        require ``file`` to be provided, whereas ``name`` is optional. If
        ``name`` is provided, then the artifact will be saved to ``file`` and
        registered in the ASDF file with the name ``name``. Already existing
        artifacts can be opened with either ``name`` or ``file``. If ``name``
        and ``file`` result in a conflict in the registered artifacts, an
        exception is raised. ``description`` is only stored in the ASDF file and
        does not impact the opened file.

        .. note::

            The list of floating artifacts is updated before the file object is
            returned. This means that before the file has been written to or
            read, the context has recorded that the artifact will exist.

        Args:
            file: Optional filename or relative path to artifact file. If None,
                an existing artifact is opened based on ``name``. Defaults to None.
            mode: The open mode of the file, passed to ``mode`` of :fun:`open`,
                internally. Defaults to "r".
            name: Optional artifact name. If None, the :fun:`io.path.basename`
                of ``file`` is used for new artifacts' names. Defaults to None.
            description: Optional description of the artifact, to be stored in
                the ASDF file. If the artifact already exists, ``description``
                is ignored. Defaults to None.
            buffering: Passed as ``buffering`` in :fun:`open`, internally.
                Defaults to -1.
            encoding: Passed as ``encoding`` in :fun:`open`, internally.
                Defaults to None.
            errors: Passed as ``errors`` to :fun:`open`, internally. Defaults to
                None.
            newline: Passes as ``newline`` to :fun:`open`, internally. Defaults
                to None.
            closefd: Passed as ``closefd`` to :fun:`open`, internally. Defaults
                to True.
            opener: Passed as ``opener`` to :fun:`open`, internally. Defaults to
                None.

        Raises:
            ValueError: If neither ``file`` nor ``name`` is provided.
            ValueError: If ``file`` is not provided and no artifact with
                ``name=name`` exists.
            RuntimeError: If another error occurred when opening the artifact
                file.

        Returns:
            A Python file object corresponding to this artifact.
        """
        ...

    def savefig(
        self,
        fig: Figure,
        file: StrOrPath | None = None,
        name: str | None = None,
        description: str | None = None,
        format: str | None = None,
        **kwargs,
    ):
        """Save a matplotlib figure as an artifact.

        Args:
            fig: The matplotlib figure to save.
            file: Optional file for the artifact. Passed to ``file`` of
                :meth:`open_artifact`. Defaults to None.
            name: Optional name for the artifact. Passed to ``name`` of
                :meth:`open_artifact`. Defaults to None.
            description: Optional description for the artifact. Passed to
                ``description`` of :meth:`open_artifact`. Defaults to None.
            format: The format of the matplotlib figure. If None and ``file`` is
                provided or the artifact already exists, the format is
                determined by the artifact ``source``. Defaults to None.
        """

        if format is None:
            # If format is None, we need to check if we can determine the
            # format.

            if self.artifacts.exists_for(file=file, name=name):
                # If the artifact exists, we get the format from the source
                # extension.
                _artifact = self.artifacts.get_for(file=file, name=name)
                source = _artifact.source
                format = source_to_figure_format(source)
            else:
                # If the artifact doesn't exist, we convert file to the source
                # and use that.
                if file is not None:
                    format = source_to_figure_format(file_to_source(file))
                else:
                    # If the artifact doesn't exist AND file is None, then we
                    # cannot save the figure. But we leave that error handling
                    # to open_artifact below.
                    format = None

        with self.open_artifact(
            file=file, mode="wb", name=name, description=description
        ) as f:
            fig.savefig(f, format=format, **kwargs)

    @abstractmethod
    def __eq__(self, value: object, /) -> bool: ...

    @abstractmethod
    def __ne__(self, value: object, /) -> bool: ...
    @abstractmethod
    def __repr__(self) -> str: ...
