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

import warnings
from datetime import datetime, timezone
from io import BufferedRandom, BufferedReader, BufferedWriter, FileIO, TextIOWrapper
from typing import IO, TYPE_CHECKING, Any, BinaryIO, Literal, NoReturn, overload
from uuid import UUID, uuid4

from aardvark.experiment.utils import (
    register_cls_bound_artifacts_with_context,
    populate_default_attrs_if_nonexistent,
)
import asdf

from aardvark.artifacts import (
    ArtifactCollection,
    ArtifactInfo,
)
from aardvark.artifacts.handlers.utils import bound_artifact_for
from aardvark.artifacts.paths import file_to_source
from aardvark.dataclasses import (
    Dataclass,
    Field,
    dataclass,
    field,
)
from aardvark.storage.base_provider import BaseContext, ContextState
from aardvark.utils.io.typeshed import (
    OpenBinaryMode,
    OpenBinaryModeReading,
    OpenBinaryModeUpdating,
    OpenBinaryModeWriting,
    OpenTextMode,
    StrOrPath,
    _Opener,
)
from matplotlib.figure import Figure

try:
    from typing import Self
except:
    from typing_extensions import Self


_getattr = object.__getattribute__
_setattr = object.__setattr__


def current_datetime() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(kw_only=True)
class Experiment(Dataclass):
    CUSTOM_SCHEMA = "asdf://aardvark.org/asdf/schemas/experiment-0.0.0"

    uuid: UUID = field(default_factory=uuid4, init=False, repr=False)
    """The unique identifier for this experiment.

    Automatically set on creating of the experiment. Can be reset with :meth:`reset`.
    """

    date_created: datetime = field(
        default_factory=current_datetime, init=False, repr=False
    )
    """The UTC date and time when this experiment was created."""

    description: str | None = field(default_factory=lambda: None, init=True, repr=True)
    """Optional description of experiment. If None, there is no description. Defaults to None."""

    @classmethod
    def __new__(cls: type[Self], *args, **kwargs) -> Self:
        __instance = super(Experiment, cls).__new__(cls)

        if "tree" in kwargs:
            _tree: asdf.AsdfFile = kwargs.pop("tree")
            populate_default_attrs_if_nonexistent(cls=cls, tree=_tree)
        else:
            _tree = asdf.AsdfFile(
                {},
                custom_schema=cls.CUSTOM_SCHEMA,
            )
        if "context" in kwargs:
            _context = kwargs.pop("context")
        else:
            from aardvark.storage import default_provider

            _context = default_provider.new_context()

        register_cls_bound_artifacts_with_context(cls=cls, context=_context)

        _setattr = object.__setattr__
        _setattr(__instance, "_tree", _tree)
        _setattr(__instance, "_tree_attrs", cls._class_tree_attrs())
        _setattr(__instance, "_context", _context)
        return __instance

    def __setattr__(self, name, value) -> None:
        if name == "_tree":
            _setattr(self, name, value)
        _tree = _getattr(self, "_tree")
        if name in _tree or name in _getattr(self, "_tree_attrs"):
            _getattr(self, "_tree")[name] = value
        else:
            _setattr(self, name, value)

    def __getattribute__(self, name):
        _tree = _getattr(self, "_tree")
        if name == "_tree":
            return _tree
        elif name in _tree or name in _getattr(self, "_tree_attrs"):
            return _tree[name]
        else:
            return _getattr(self, name)

    @property
    def artifacts(self) -> ArtifactCollection:
        return self._context.artifacts

    def __post_init__(self):
        self.validate()
        self._after_create()

    def reset(self):
        """Reset uuid, date_created, and location; but not experiment data."""
        # To not repeat ourselves, call the default factory from __dataclass_fields__.
        self.uuid = self.__dataclass_fields__["uuid"].default_factory()
        self.date_created = self.__dataclass_fields__["date_created"].default_factory()

    def set_date_created(self, date_created: datetime | None = None):
        """Set :attr:`date_created` to the provided date or to the current date and time.

        Args:
            date_created: Optional new date_created value. If None, then
            `datetime.now()` at UTC is used. Defaults to None.
        """
        self.date_created = (
            date_created
            if date_created is not None
            else self.__dataclass_fields__["date_created"].default_factory()  # type: ignore
        )

    def validate(self):
        """Validate :class:`Experiment` instance.

        Called by :meth:`__init__` and :meth:`update_class`. When overriding,
        make sure to call the super validation method.
        """
        pass

    @classmethod
    def _class_tree_attrs(cls) -> set[str]:
        return set(cls.__dataclass_fields__.keys())

    @classmethod
    def _class_artifact_attrs(cls) -> set[str]:
        return {
            attr_name
            for attr_name, attr_field in cls.__dataclass_fields__.items()
            if "artifact_info" in attr_field.metadata
        }

    @classmethod
    def _class_artifact_metadata(cls) -> dict[str, dict[str, Any]]:
        """Dictionary of bound artifact metadata defined for this class.

        Keys are attribute names.

        Returns:
            Metadata associated with bound artifacts.
        """
        artifact_metadatas: dict[str, dict[str, Any]] = {}
        for artifact_attr in cls._class_artifact_attrs():
            _field: Field
            _field = cls.__dataclass_fields__[artifact_attr]
            artifact_metadatas[artifact_attr] = _field.metadata["artifact_info"]
        return artifact_metadatas

    def _after_load(self):
        pass

    def _before_save(self):
        pass

    def _after_save(self, success: bool):
        pass

    def _after_create(self):
        pass

    def register_tree_attribute(self, attr_name: str):
        """Register the attribute ``attr_name`` as a tree attribute.

        All registered attributes are accessible as ``instance.<attr_name>``.
        Their values will be saved in the ASDF tree under the ``"attr_name"``
        key. Registered attributes can be deregistered with
        :meth:`deregister_tree_attribute`.

        Args:
            attr_name: The name of the attribute to save in the ASDF tree.
        """
        if attr_name in self._tree_attrs:
            warnings.warn("Attribute is already registered.")
        else:
            # Check if we have set the value on this instance. If yes,
            # transfer the value to the tree.
            _has_value = False
            _value = None
            try:
                _value = object.__getattribute__(self, attr_name)
                delattr(self, attr_name)
                _has_value = True
            except AttributeError:
                pass
            self._tree_attrs.add(attr_name)
            if _has_value:
                setattr(self, attr_name, _value)

    def deregister_tree_attribute(self, attr_name: str):
        """Deregister the attribute ``attr_name`` so it isn't saved in the ASDF
           file.

        Registered attributes are attributes that are added at runtime and not
        in the class definition. They were added with
        :meth:`register_tree_attribute`. Upon deregistration, their value is
        moved to a normal instance attribute, still accessible with
        ``instance.<attr_name>``.

        Args:
            attr_name: The name of the attribute to deregister.

        Raises:
            AttributeError: If the attribute name is a class attribute.
            AttributeError: If the attribute name is not registered.
        """
        if attr_name in self._class_tree_attrs():
            raise AttributeError("Cannot deregister class tree attribute")
        if attr_name in self._tree_attrs:
            self._tree_attrs.remove(attr_name)
            # This is a bit of a hack as ASDF doesn't support deleting tree entries.
            _value = self._tree._tree.pop(attr_name)
            setattr(self, attr_name, _value)
            return
        raise AttributeError("Attribute '{}' not registered.".format(attr_name))

    @classmethod
    def load(cls, file: StrOrPath, call_validate: bool = True) -> Self:
        from aardvark.storage.folder_provider import FolderContext

        _tree, _context = FolderContext.load(file)
        _inst = cls.__new__(cls, context=_context, tree=_tree)
        _inst._after_load()
        if call_validate:
            _inst.validate()
        _inst._after_create()
        return _inst

    def save(self, overwrite: bool = True):
        try:
            self._before_save()
            self._context.save(self, overwrite=overwrite)
        except Exception as e:
            self._after_save(False)
            raise RuntimeError("Failed to save experiment.") from e
        self._after_save(True)

    def get_artifact_path(
        self,
        file: StrOrPath | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> str:
        try:
            if file is None and name is None:
                raise ValueError(
                    "At least file or name must be provided when opening an existing artifact."
                )

            if file is not None:
                _source = file_to_source(file)
            else:
                _source = None

            _add_artifact = False
            if self.artifacts.exists_for(source=_source, name=name):
                # Opening existing artifact. Get its source instead of using
                # _source as _source may be None.
                _artifact = self.artifacts.get_for(source=_source, name=name)
                _file = _artifact.source
            elif file is not None:
                # We are creating a new artifact, so set _file to file.
                _file = file
                _add_artifact = True
            else:
                # Attempting to create an artifact but no file path given.
                raise ValueError("Cannot create artifact without a file path.")

            _artifact_path = self._context.get_artifact_path(
                experiment=self,
                file=_file,
            )
            # File was created successfully. Create and register artifact if it doesn't already exist.
            if _add_artifact:
                _artifact = ArtifactInfo(file=_file, name=name, description=description)
                self.artifacts._add_artifact(artifact=_artifact)

            # Return the opened file.
            return _artifact_path
        except Exception as e:
            raise RuntimeError("Failed to open artifact.", e)

    # Text mode: always returns a TextIOWrapper
    @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: OpenTextMode = "r",
        name: str | None = None,
        description: str | None = None,
        postpone_save: bool = ...,
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
        postpone_save: bool = ...,
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
        postpone_save: bool = ...,
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
        postpone_save: bool = ...,
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
        postpone_save: bool = ...,
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
        postpone_save: bool = ...,
        buffering: int = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> BinaryIO: ...

    # Fallback if mode is not specified
    # @overload
    def open_artifact(
        self,
        file: StrOrPath | None = None,
        mode: str = "r",
        name: str | None = None,
        description: str | None = None,
        postpone_save: bool = False,
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        closefd: bool = True,
        opener: _Opener | None = None,
    ) -> IO[Any]:
        """Open a floating rtifact as a Python file, saving as a floating
           artifact if necessary.

        If the artifact was never opened, a new file is created. New artifacts
        require ``file`` to be provided, whereas ``name`` is optional. If
        ``name`` is provided, then the artifact will be saved to ``file`` and
        registered in the ASDF file with the name ``name``. Already existing
        artifacts can be opened with either ``name`` or ``file``. If ``name``
        and ``file`` result in a conflict in the registered artifacts, an
        exception is raised. ``description`` is only stored in the ASDF file and
        does not impact the opened file.

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
            postpone_save: If False, and the experiment has already been saved
                or was loaded from an existing file, then the experiment is
                saved too. This is to ensure the list of floating artifacts is
                updated with this figure. If True, then this does not happen but
                the user must call :meth:`save` to ensure the list of artifacts
                is saved to the ASDF file. If the artifact already exists, then
                the experiment is never saved and ``postpone_save`` does
                nothing. Defaults to False.
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
        _exists = self.artifacts.exists_for(file=file, name=name)
        _artifact = self._context.open_artifact(
            file=file,
            mode=mode,
            name=name,
            description=description,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )

        # We save so we correctly record the artifact in the ASDF file. This
        # prevents having to call `exp.save()` after opening and writing to an
        # artifact. However, we only need to do this if the artifact did not
        # exist beforehand.
        if (
            not _exists
            and not postpone_save
            and self._context.state == ContextState.saved
        ):
            self.save()

        return _artifact

    def savefig(
        self,
        fig: Figure,
        file: StrOrPath | None = None,
        name: str | None = None,
        description: str | None = None,
        format: str | None = None,
        postpone_save: bool = False,
        **kwargs,
    ):
        """Save a matplotlib figure as an artifact.

        ``file`` and ``name`` are used to determine how to save the figure. If
        an artifact for that file and with that name already exists, the figure
        is saved to that artifact. If such an artifact does not exist, one is
        created and thus ``file`` is required. If ``format`` is None, then the
        format for the figure is determined from ``file``, or the associated
        artifact's :attr:`aardvark.artifacts.ArtifactInfo.source``. ``format``
        can be overridden by setting it to a string compatible with
        :meth:`matplotlib.figure.Figure.savefig`. Additional arguments are
        passed to :meth:`matplotlib.figure.Figure.savefig`.

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
            postpone_save: If False, and the experiment has already been saved
                or was loaded from an existing file, then the experiment is
                saved too. This is to ensure the list of floating artifacts is
                updated with this figure. If True, then this does not happen but
                the user must call :meth:`save` to ensure the list of artifacts
                is saved to the ASDF file. If the artifact already exists, then
                the experiment is never saved and ``postpone_save`` does
                nothing. Defaults to False.
        """
        self._context.savefig(
            fig=fig,
            file=file,
            name=name,
            description=description,
            format=format,
            **kwargs,
        )

        if not postpone_save and self._context.state == ContextState.saved:
            self.save()

    def __eq__(self, value: "Experiment", /) -> bool:
        if not isinstance(value, Experiment):
            raise ValueError(
                "Cannot compare {} to {}.".format(self.__class__.__name__, type(value))
            )
        return self._tree == value._tree and self._context == value._context
