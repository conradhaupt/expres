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
from collections.abc import Iterable, Iterator
from typing import Literal, NoReturn

from aardvark.artifacts.typing import ArtifactFormat
from aardvark.utils.io import StrOrPath_to_Path, could_be_file_path
from aardvark.utils.io.typeshed import StrOrPath

from .artifact import ArtifactInfo
from .paths import file_to_source, norm_name, norm_source
from .typing import NameStr, SourceStr

try:
    from typing import overload
except ImportError:
    from typing_extensions import overload


class ArtifactCollection(Iterable[str]):
    """Custom collection of artifacts."""

    def __init__(self, artifacts: list[ArtifactInfo] | None = None) -> None:
        """Create an artifact collection, with optional initial artifacts.

        Args:
            artifacts: Optional list of artifacts to include in this collection.
                If None, the collection starts empty. Defaults to None.
        """
        self._artifacts: dict[SourceStr, ArtifactInfo] = {}
        self._name_source_mapping: dict[NameStr, SourceStr] = {}
        if artifacts is not None:
            for _artifact in artifacts:
                self._add_artifact(artifact=_artifact)

    @overload
    def _add_artifact(
        self,
        file: None = ...,
        name: None = ...,
        description: None = ...,
        format: None = ...,
        floating: bool = ...,
        artifact: ArtifactInfo = ...,
    ) -> None: ...
    @overload
    def _add_artifact(
        self,
        file: StrOrPath = ...,
        name: str | None = ...,
        description: str | None = ...,
        format: None = ...,
        floating: Literal[True] = ...,
        artifact: None = ...,
    ) -> None: ...
    @overload
    def _add_artifact(
        self,
        file: StrOrPath = ...,
        name: str = ...,
        description: str | None = ...,
        format: ArtifactFormat = ...,
        floating: Literal[False] = ...,
        artifact: None = ...,
    ) -> None: ...
    def _add_artifact(
        self,
        file: StrOrPath | None = None,
        name: str | None = None,
        description: str | None = None,
        format: ArtifactFormat | None = None,
        floating: bool = True,
        artifact: ArtifactInfo | None = None,
    ) -> None:
        """Add an artifact.

        Equality between :class:`~pathlib.Path` instances are used to compare
        :attr:`ArtifactInfo.source` values. If a conflict occurs, an error is
        raised.

        Artifacts are added by the relative path to their file when the
        experiment is saved: ``file``. An optional ``name`` parameter overrides
        the default artifact name, which is the basename of ``file``. An
        optional description is included as metadata in the saved ASDF file.
        Alternatively, one can pass an already existing :class:`ArtifactInfo`
        instance to ``artifact``.

        Note that all artifacts added with ``file`` and not ``artifact`` are
        added as a floating artifact.

        Args:
            file: Relative path to the file. Can only be used if ``artifact`` is
                None. Creates a floating artifact.
            name: Optional name of the artifact. If None, the filename from
                ``file`` is used. Can only be used if ``artifact`` is None.
                Defaults to None.
            description: Optional description for the artifact, which is stored
                in the final ASDF file. Can only be used if ``artifact`` is
                None. Defaults to None.
            format: The format for bound artifacts. If not None, then
                ``floating`` must be False. If None, then ``floating`` must be
                True. Defaults to None.
            floating: If the artifact, created with ``file``, is floating. If
                ``artifact`` is not None, then ``floating`` is ignored. Defaults
                to True.
            artifact: Optional :class:`ArtifactInfo` object to add. If provided,
                ``file``, ``name``, and ``description`` must be None. If
                ``file`` is not None, ``artifact`` must be None. Defaults to
                None.

        Raises:
            ValueError: If the name already exists.
            ValueError: If an artifact with an equivalent source already exists.
            ValueError: If neither file or artifact is passed.
            ValueError: If file, name, or description is passed and an
            :class:`ArtifactInfo` instance is provided.
        """
        if artifact is not None:
            if file is not None:
                raise ValueError("Cannot pass file and an ArtifactInfo instance.")
            if name is not None:
                raise ValueError("Cannot pass name and an ArtifactInfo instance.")
            if description is not None:
                raise ValueError(
                    "Cannot pass description and an ArtifactInfo instance."
                )
            if format is not None:
                raise ValueError("Cannot pass format and an ArtifactInfo instance.")
        else:
            if file is None:
                raise ValueError("file or artifact must be passed, but neither was.")
            if floating:
                if format is not None:
                    raise ValueError("Cannot create floating artifact with a format.")
                artifact = ArtifactInfo(
                    file=file,
                    name=name,
                    description=description,
                    format=format,
                    floating=floating,
                )
            else:
                if format is None:
                    raise ValueError("Cannot create bound artifact without format.")
                if name is None:
                    raise ValueError(
                        "Cannot create bound artifact without a name. "
                        + "This should be the name of the attribute to which the artifact is bound."
                    )
                artifact = ArtifactInfo(
                    file=file,
                    name=name,
                    description=description,
                    format=format,
                    floating=floating,
                )

        if artifact.name in self._name_source_mapping:
            raise ValueError("An artifact with this name already exists.")
        if artifact.source in self._artifacts:
            raise ValueError("An artifact with this source already exists.")

        self.__unsafe_add_artifact(artifact)

    def __unsafe_add_artifact(self, artifact: ArtifactInfo):
        """Internal methods to add artifacts from the collection.

        Manages both _artifacts and _name_source_mapping at the same time. Does
        not implement checks for the existence of artifacts.
        """
        self._artifacts[norm_source(artifact.source)] = artifact
        self._name_source_mapping[norm_name(artifact.name)] = norm_source(
            artifact.source
        )

    def __unsafe_remove_artifact(self, artifact: ArtifactInfo):
        """Internal methods to remove artifacts from the collection.

        Manages both _artifacts and _name_source_mapping at the same time. Does
        not implement checks for the existence of artifacts.
        """
        del self._artifacts[norm_source(artifact.source)]
        del self._name_source_mapping[norm_name(artifact.name)]

    @overload
    def _remove_artifact(
        self,
        name: str = ...,
        source: None = ...,
        artifact: None = ...,
    ) -> None: ...
    @overload
    def _remove_artifact(
        self,
        name: None = ...,
        source: str = ...,
        artifact: None = ...,
    ) -> None: ...
    @overload
    def _remove_artifact(
        self,
        name: str = ...,
        source: str = ...,
        artifact: None = ...,
    ) -> None | NoReturn: ...
    @overload
    def _remove_artifact(
        self,
        name: None = ...,
        source: None = ...,
        artifact: ArtifactInfo = ...,
    ) -> None: ...
    @overload
    def _remove_artifact(
        self,
        name: None = ...,
        source: None = ...,
        artifact: None = ...,
    ) -> NoReturn: ...
    def _remove_artifact(
        self,
        name: str | None = None,
        source: str | None = None,
        artifact: ArtifactInfo | None = None,
    ) -> None | NoReturn:
        """Remove an artifact by name, source, or the :class:`ArtifactInfo` instance.

        Args:
            name: Optional name identifying the artifact to remove. If None,
                ``source`` or ``artifact`` must be provided. Defaults to None.
            source: Optional source identifying the artifact to remove. If None,
                ``name`` or ``artifact`` must be provided. Defaults to None.
            artifact: Optional :class:`ArtifactInfo` identifying the artifact to
                remove. If None, ``name`` or ``source`` must be provided.
                Defaults to None.

        Raises:
            ValueError: If neither ``name`` or ``source`` is provided and
                ``artifact`` is None.
            KeyError: If ``name`` is not None but no artifact has that name.
            KeyError: If ``source`` is not None but no artifact has source equal
                to ``source``.
            KeyError: If ``artifact`` is not None but no artifact has the same
                source or name.
        """
        # Validate exclusive parameter setting
        if name is not None and artifact is not None:
            raise ValueError("name and artifact cannot be provided together.")
        if source is not None and artifact is not None:
            raise ValueError("source and artifact cannot be provided together.")

        # Remove artifacts
        if name is not None and source is not None:
            # We have both name and source, so we check that the artifacts are the same.
            _name_artifact = self.__artifact_by_name(name)
            _source_artifact = self.__artifact_by_source(source)
            if _name_artifact != _source_artifact:
                raise KeyError("name and source refer to different artifacts.")

            # Remove artifact
            self.__unsafe_remove_artifact(_source_artifact)
        elif name is not None:
            # We only have source.

            # This will raise a KeyError if no artifact with that name exists
            artifact = self.__artifact_by_name(name)

            # Remove artifact
            self.__unsafe_remove_artifact(artifact)
        elif source is not None:
            # We only have name.

            # This will raise a KeyError if no artifact with that source exists
            artifact = self.__artifact_by_source(source)

            # Remove artifact
            self.__unsafe_remove_artifact(artifact)
        elif artifact is not None:
            # We have an artifact.

            # Confirm that such an artifact exists.
            if norm_name(artifact.name) not in self._name_source_mapping:
                raise KeyError("No artifact found for name {!r}".format(artifact.name))
            if norm_source(artifact.source) not in self._artifacts:
                raise KeyError(
                    "No artifact found for source {!r}".format(artifact.source)
                )

            # Confirm that the name refers to the correct source
            if (
                norm_source(artifact.source)
                != self._name_source_mapping[norm_name(artifact.name)]
            ):
                raise KeyError(
                    "Stored artifact with that name refers to a different source."
                )

            # Remove artifact
            self.__unsafe_remove_artifact(artifact)
        else:
            raise ValueError("Exactly one of name, source, artifact must be not None.")

    def __artifact_by_name(self, name: str) -> ArtifactInfo:
        _name = norm_name(name)
        if _name not in self._name_source_mapping:
            raise KeyError("No artifact found for name {!r}".format(name))
        _source = self._name_source_mapping[_name]
        return self._artifacts[_source]

    def __artifact_by_source(self, source: str) -> ArtifactInfo:
        _source = norm_source(source)
        if _source not in self._artifacts:
            raise KeyError("No artifact found for source {!r}".format(source))
        return self._artifacts[_source]

    def artifacts(self) -> list[ArtifactInfo]:
        """List of artifacts stored in this collection."""
        return list(self._artifacts.values())

    def names(self) -> list[str]:
        """List of artifact names for artifacts stored in this collection."""
        return list(self._name_source_mapping.keys())

    def __getitem__(self, name: str) -> ArtifactInfo:
        return self.__artifact_by_name(name)

    def __iter__(self) -> Iterator[ArtifactInfo]:
        yield from self._artifacts.values()

    @overload
    def exists_for(
        self,
        file: StrOrPath | None = ...,
        source: None = ...,
        name: str | None = ...,
    ) -> bool: ...
    @overload
    def exists_for(
        self,
        file: None = ...,
        source: str | None = ...,
        name: str | None = ...,
    ) -> bool: ...
    def exists_for(
        self,
        file: StrOrPath | None = None,
        source: str | None = None,
        name: str | None = None,
    ) -> bool:
        """Whether an artifact is stored with the given optional source and/or name.

        Args:
            file: Optional file path for the artifact, instead of ``source``. If
                None, artifacts are identified only on their name. This or
                ``source`` must be provided if ``name`` is None. Defaults to
                None.
            source: Optional source for the artifact, instead of ``file. If
                None, artifacts are identified only on their name. This or
                ``file`` must be provided if ``name`` is None. Defaults to None.
            name: Optional name for the artifact. If None, artifacts are
                identified only on their source. Must be provided if ``source``
                is None. Defaults to None.

        Raises:
            ValueError: If neither ``source`` nor ``name`` is provided.

        Returns:
            Whether an artifact with the given ``source`` and ``name`` exists.
            If either is None, that attribute is not used in identifying the
            artifact.
        """
        if file is not None:
            if source is not None:
                raise ValueError("Either file or source can be provided, not both.")
            source = file_to_source(file)
        _source_or_none = self.__source_for_existing_or_none(source=source, name=name)
        if _source_or_none is None:
            return False
        return True

    def __source_for_existing_or_none(
        self, source: str | None = None, name: str | None = None
    ) -> SourceStr | None:
        """Returns the source for an artifact with ``name`` and ``source``, or
           None if no such artifact exists.

        Note that if an artifact exists with the same source or name, but the
        other does not match, then None is still returned.

        Args:
            source: Optional source for the artifact. If None, only ``name`` is
                used to find the artifact. Defaults to None.
            name: Optional name for the artifact. If None, only ``source`` is
                used to find the artifact. Defaults to None.

        Raises:
            ValueError: If neither ``source`` nor ``name`` is provided.

        Returns:
            The source for the artifact, identified by ``source`` and ``name``,
            or None.
        """
        if source is not None:
            # Check based on source
            if norm_source(source) in self._artifacts:
                _artifact = self.__artifact_by_source(source)

                # Check that name matches, if we were given a name
                if name is not None and _artifact.name != name:
                    return None

                # Either name wasn't provided or it matches
                return norm_source(source)
            else:
                # Source doesn't exist
                return None
        elif name is not None:
            _name = norm_name(name)
            if _name in self._name_source_mapping:
                # Name exists in mapping, and it _should_ therefore have an
                # artifact with the mapped source.
                return self._name_source_mapping[_name]
            else:
                # Name doesn't exist in mappings
                return None
        else:
            raise ValueError("At least one of 'source' or 'name' must be not None.")

    def get_for(
        self,
        file: StrOrPath | None = None,
        source: str | None = None,
        name: str | None = None,
    ) -> ArtifactInfo:
        """Get an artifact the given source and name.

        If either ``source`` or ``name`` is None, that attribute is ignored when
        getting the artifact. If both are provided, then both must match the
        artifact.

        Args:
            file: Optional file for the artifact, instead of ``source``. If
                None, and ``source`` is also None, the artifact is chosen based
                on its name. Defaults to None.
            source: Optional source of the artifact. If None, and ``file`` is
                also None, the artifact is chosen based on its name. Defaults to
                None.
            name: Optional name of the artifact. If None, the returned artifact
                is selected on ``source`` or ``file``.

        Raises:
            KeyError: If no artifact is found.

        Returns:
            The registered artifact instance corresponding to the given ``file``
            or ``source``, and/or ``name`` values.
        """
        if file is not None:
            if source is not None:
                raise ValueError("Either source or file can be provided, not both.")
            source = file_to_source(file)
        _source_or_none = self.__source_for_existing_or_none(source=source, name=name)
        if _source_or_none is None:
            if source is None:
                raise KeyError("Cannot find artifact with name {!r}".format(name))
            elif name is None:
                raise KeyError("Cannot find artifact with source {!r}".format(source))
            else:
                raise KeyError(
                    "Cannot find artifact with name {!r} and source {!r}".format(
                        name, source
                    )
                )
        else:
            return self._artifacts[_source_or_none]

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, ArtifactCollection):
            raise ValueError(
                "Cannot compare ArtifactCollection to {!r}".format(type(value))
            )
        return (self._artifacts == value._artifacts) and (
            self._name_source_mapping == value._name_source_mapping
        )

    def __repr__(self) -> str:
        num_artifacts = 0
        num_bound_artifacts = 0
        num_floating_artifacts = 0
        for _artifact in self._artifacts.values():
            num_artifacts += 1
            if _artifact.is_bound():
                num_bound_artifacts += 1
            else:
                num_floating_artifacts += 1
        return "{}(num_artifacts={}, num_bound_artifacts={}, num_floating_artifacts={})".format(
            self.__class__.__name__,
            num_artifacts,
            num_bound_artifacts,
            num_floating_artifacts,
        )

    @property
    def num_artifacts(self) -> int:
        """The total number of artifacts in this collection."""
        return len(self.artifacts())

    @property
    def num_bound_artifacts(self) -> int:
        """The number of bound artifacts in this collection."""
        return len(self.bound_artifacts())

    @property
    def num_floating_artifacts(self) -> int:
        """The number of floating artifacts in this collection."""
        return len(self.floating_artifacts())

    def bound_artifacts(self) -> list[ArtifactInfo]:
        """List of bound artifacts in this collection."""
        return [
            _artifact for _artifact in self._artifacts.values() if _artifact.is_bound()
        ]

    def floating_artifacts(self) -> list[ArtifactInfo]:
        """List of floating artifacts in this collection."""
        return [
            _artifact
            for _artifact in self._artifacts.values()
            if _artifact.is_floating()
        ]
