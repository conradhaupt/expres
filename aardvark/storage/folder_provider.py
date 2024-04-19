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

import logging
import re
from datetime import datetime
from datetime import timezone as tz
from io import BufferedRandom, BufferedReader, BufferedWriter, FileIO, TextIOWrapper
from pathlib import Path
from shutil import copy2
from sys import version_info
from tempfile import mkdtemp
from typing import IO, TYPE_CHECKING, Any, BinaryIO, Literal, TypeVar, overload
from uuid import UUID

from asdf import AsdfFile
from asdf import open as asdf_open

from aardvark.artifacts import ArtifactInfo
from aardvark.artifacts.artifact import ArtifactInfo
from aardvark.artifacts.artifact_collection import ArtifactCollection
from aardvark.artifacts.handlers.utils import handler_for
from aardvark.artifacts.typing import SourceStr
from aardvark.artifacts.utils import (
    artifacts_from_asdf,
    replace_values_with_artifacts,
    restore_values_for_artifacts,
)
from aardvark.config import get_config
from aardvark.storage.base_provider import BaseContext, BaseProvider, ContextState
from aardvark.utils.io.typeshed import (
    OpenBinaryMode,
    OpenBinaryModeReading,
    OpenBinaryModeUpdating,
    OpenBinaryModeWriting,
    OpenTextMode,
    StrOrPath,
    _Opener,
)

if version_info[1] <= 11:
    from typing_extensions import override
else:
    from typing import override

if version_info[1] <= 10:
    from typing_extensions import Self
else:
    from typing import Self


if TYPE_CHECKING:
    from aardvark import Experiment


logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="Experiment")


def mkdtemp_contextdir() -> Path:
    """Creates a new temporary directory and returns an absolute Path to it.

    If ``storage_providers.folder_storage_provider.temp_dir`` is not None, then
    the temporary directory will be created in that folder. If it is None, then
    the system temporary directory location is determined with
    :meth:`tempfile.mkdtemp`. Folders have the prefix ``aardvark_<date>`` where
    ``<date>`` is the current date and time upon creation, at UTC.

    Returns:
        The Path object to the temporary directory.
    """
    config = get_config()
    dir_config = config["storage_providers"]["folder_storage_provider"]["temp_dir"]
    return Path(
        mkdtemp(
            prefix="aardvark_{date:%Y%m%d_%H%M%S}_".format(date=datetime.now(tz.utc)),
            dir=Path(dir_config).expanduser() if dir_config is not None else None,
        )
    ).absolute()


def transformed_description(description: str | None, max_length: int) -> str:
    """Transform a description into a string appropriate for folder and file names.

    This function converts ``description`` into a single-line string where
    spaces are replaced by underscores. Repeated spaces are replaced with a
    single underscore. The maximum length of the output is dictated by
    ``max_length``. The description is truncated on word boundaries to fit
    within ``max_length``.

    As this function returns the value for ``"{desc}"`` in the config's filename
    and folder format strings, it must have an underscore as a prefix.

    Args:
        description: The description string for an experiment, which can be a
            multiline string. If None, an empty string is returned.
        max_length: The maximum length of the output in number of characters.
    """
    # If description is None, we don't have to format anything.
    if description is None:
        return ""
    # If the max length is less than two, we don't have to do anything.
    if max_length < 1:
        return ""
    values = re.sub(r"\ +", " ", re.sub(r"\r\n|\n|\r", "", description)).split(" ")
    output: list[str] = []
    # We start from one for the prefix underscore.
    output_length = 1
    # Build a shortened description by adding words until we reach the maximum
    # length.
    for v in values:
        # If the stripped word is now empty, skip it.
        if len(v) == 0:
            continue

        if output_length + 1 > max_length:
            # If adding any word, which would require a new separator, would
            # exceed the max length, then break and return the description.
            break
        elif output_length + 1 + len(v) > max_length:
            # If adding the current word would exceed the max length, add a
            # truncated version.

            # Check the length of the word to add.
            _len = max_length - output_length
            # If we already have words, we need a separator.
            if len(output) > 0:
                _len -= 1
            # If the length of the word to add is zero, then we ignore it and
            # just return the current description.
            if _len == 0:
                break
            output.append(v[:_len])
            break
        else:
            # We have more than enough remaining space, so add the word and continue.
            if len(output) > 0:
                output_length += 1
            output_length += len(v)
            output.append(v)

    # Return the selected words with "_" separators and the prefix "_". If
    # output is empty, we return "" instead.
    _output = "_".join(output)
    if len(_output) > 0:
        return "_" + _output
    return ""


def target_path_for(
    experiment: "Experiment | AsdfFile",
    experiment_name: str | None = None,
    location: Path | None = None,
    root_dir: str | None = None,
    folder_format: str | None = None,
    filename_format: str | None = None,
) -> Path:
    """Compute the absolute path for the given experiment.

    The target path for the ASDF file is determined as follows, in decreasing
    precedence.

    A) If ``location`` is provided, then the target path is
       ``location/filename_format``, formatted with values from ``experiment``.

    B) If ``location`` is None, then the location is equivalent to
       ``root_dir/folder_format/filename_format``.

    C) If any of these three variables are None, their value is retrieved from
       the current config. For example, if only ``folder_format`` and
       ``filename_format`` are provided, then the path will be to
       ``folder_format/filename_format`` relative to ``root_dir`` retrieved from
       the current config.

    Args:
        experiment: The experiment or associated AsdfFile tree whose filename
            should be computed.
        experiment_name: Optional name for the experiment type. If
            ``experiment`` is an instance of
            :class:`aardvark.experiment.Experiment`, this is the subclass name.
            If ``experiment`` is an instance of :class:`~asdf.AsdfFile` and
            ``experiment_name`` is None, then ``"Experiment"`` is used. Defaults
            to None.
        location: Optional path to the experiment folder. If None, ``root_dir``
            and ``folder_format`` are used. Defaults to None.
        root_dir: Optional path to data directory. If ``location`` is provided,
            it is used to determine the target path instead of ``root_dir`` and
            ``folder_format``. If None, ``root_dir`` is retrieved from the
            current config using :fun:`get_config`. Defaults to None.
        folder_format: Optional format string. If ``location`` is provided, it
            is used to determine the target path instead of ``root_dir`` and
            ``folder_format``. If None, ``folder_format`` is retrieved from the
            current config using :fun:`get_config`. Defaults to None.
        filename_format: Optional format string. If None, ``filename_format`` is
            retrieved from the current config using :fun:`get_config`. Defaults
            to None.

    Raises:
        ValueError: If ``experiment`` is neither an instance of
        :class:`Experiment` nor :class`AsdfFile`.

    Returns:
        The filename for this experiment, conforming to the currently
        relevant FolderProvider config.
    """
    # Handle experiment_name and convert Experiment instances to just an
    # AsdfFile for simpler code.
    if isinstance(experiment, AsdfFile):
        if experiment_name is None:
            _experiment_name = "Experiment"
        _experiment: AsdfFile = experiment
    elif hasattr(experiment, "_tree") and isinstance(experiment._tree, AsdfFile):
        if experiment_name is None:
            _experiment_name = experiment.__class__.__name__

        # We don't want to import Experiment as this causes a cyclic import. So
        # we check if it has a _tree attribute. This should be an AsdfFile.
        _experiment = experiment._tree
    else:
        raise ValueError("experiment must be an instance of Experiment or AsdfFile.")

    return format_path(
        experiment_name=_experiment_name,
        date_created=_experiment["date_created"],
        uuid=_experiment["uuid"],
        description=_experiment["description"],
        location=location,
        root_dir=root_dir,
        folder_format=folder_format,
        filename_format=filename_format,
    )


def format_path(
    experiment_name: str,
    date_created: datetime,
    uuid: UUID,
    description: str | None = None,
    location: Path | None = None,
    root_dir: str | None = None,
    folder_format: str | None = None,
    filename_format: str | None = None,
) -> Path:
    """Return the formatted path for the given experiment ASDF file.

    Args:
        experiment_name: The name of the experiment class.
        date_created: The date on which this experiment was created.
        uuid: The UUID for this experiment.
        description: Optional description for this experiment. Defaults to None.
        location: Optional location to the experiment folder. If provided,
            ``root_dir`` and ``folder_format`` are ignored. Defaults to None.
        root_dir: Optional formatting string for the root. If ``location`` is
            provided, this is ignored. If None, retrieved from the aardvark config
            with :fun:`aardvark.config.get_config`. Defaults to None.
        folder_format: Optional formatting string for the folder. If
            ``location`` is provided, this is ignored. If None, retrieved from the
            aardvark config with :fun:`aardvark.config.get_config`. Defaults to
            None.
        filename_format: Optional formatting string for the filename. If None,
            retrieved from the aardvark config with
            :fun:`aardvark.config.get_config`. Defaults to None.

    Returns:
        Formatted path to the asdf file.
    """
    config = get_config()
    # Get experiment attributes to pass to format strings.
    desc = transformed_description(
        description,
        config["storage_providers"]["folder_storage_provider"][
            "description_max_length"
        ],
    )
    uuid_short = uuid.hex[:8]

    # Get parts of path, combine, and return
    _format_kwargs = {
        "date_created": date_created,
        "experiment_name": experiment_name,
        "desc": desc,
        "uuid_short": uuid_short,
    }

    # Load missing parameters from the current config
    if location is None:
        if root_dir is None:
            root_dir = config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ]
        if folder_format is None:
            folder_format = config["storage_providers"]["folder_storage_provider"][
                "folder_format"
            ]
        location = Path(root_dir).joinpath(Path(folder_format.format(**_format_kwargs)))
    if filename_format is None:
        filename_format = config["storage_providers"]["folder_storage_provider"][
            "filename_format"
        ]

    _filename = filename_format.format(**_format_kwargs)
    _path = location.joinpath(Path(_filename)).expanduser()
    return _path


class FolderContext(BaseContext):
    _current_path: Path
    """The current path to the ASDF file.

    If :attr:`_state` is :attr:`ContextState.unsaved`, then
    :attr:`_current_path` refers to where the ASDF file would be saved in a
    temporary directory. If :attr:`_state` is :attr:`ContextState.saved`, then
    :attr:`_current_path` refers to where the ASDF file is saved, i.e., also the
    target path.

    If :attr:`_state` is :attr:`ContextState.staging`, then
    :attr:`_current_path` depends on the previous state and should not be used
    outside of :meth:`save` and :meth:`load`.
    """

    def __init__(
        self,
        current_path: Path | None = None,
        state: ContextState | None = None,
        artifacts: ArtifactCollection | None = None,
    ):
        """Initialise a new FolderContext.

        Args:
            current_path: Optional path to an experiment ASDF file. If None, a
                temporary directory is created. Defaults to None.
            state: Optional state of the context. If None, the default set by
                :class:`BaseContext` is used. Defaults to None.
            artifacts: Optional artifact collection. If None, the context starts
                with no artifacts. Defaults to None.
        """
        super().__init__()
        self._artifacts_to_move: set[SourceStr] = set()
        if current_path is None:
            current_path = mkdtemp_contextdir().joinpath(Path("temp_experiment.asdf"))
        self._current_path = current_path

        # These attributes are set in __new__ but we can override them here.
        if state is not None:
            self._state = state
        if artifacts is not None:
            self.artifacts = artifacts

    @classmethod
    def load(cls, file: StrOrPath) -> tuple[AsdfFile, Self]:
        """Load an experiment from ``file``.

        Args:
            file: The path to the asdf file to be loaded.

        Returns:
            The loaded ASDF file and its associated context.
        """

        asdf_path = Path(file).expanduser()
        tree = asdf_open(
            fd=asdf_path,
            custom_schema="asdf://aardvark.org/asdf/schemas/experiment-0.0.0",
        )
        artifacts = tree["artifacts"]
        # We delete "artifacts" from the tree so we only store them in the context.
        del tree._tree["artifacts"]
        context = cls(
            current_path=asdf_path,
            state=ContextState.saved,
            artifacts=artifacts,
        )

        # Load bound artifacts
        bound_artifacts = artifacts_from_asdf(tree)
        for _artifact in bound_artifacts:
            logger.info("Loading bound artifact for attr %r", _artifact.attr)

            # Get path to artifact and confirm it exists
            _artifact_path = asdf_path.parent.joinpath(Path(_artifact.source))
            if not _artifact_path.exists():
                raise FileNotFoundError(
                    "Cannot find file for bound artifact {!r}: {!r}".format(
                        _artifact.attr, _artifact_path
                    )
                )

            # Get artifact handler, load object, assign to tree, and record
            # artifact in context.
            _handler = handler_for(_artifact)
            _obj = _handler.load_obj_from(_artifact_path)
            context.artifacts._add_artifact(artifact=_artifact)
            tree[_artifact.attr] = _obj

        # Return tree and appropriate context.
        return tree, context

    def save(
        self,
        experiment: "Experiment | AsdfFile",
        overwrite: bool = False,
        folder: str | None = None,
        asdf_write_to_kwargs: dict[str, Any] = {},
    ):
        """Save an experiment or ASDF tree to a folder, with its artifacts.

        Args:
            experiment: The experiment or ASDF tree to save.
            overwrite: Whether to overwrite an already existing file. Defaults
                to False.
            folder: Optional folder into which the experiment should be saved. A
                subfolder is created inside ``folder`` for the experiment.
                Defaults to None.
            asdf_write_to_kwargs: Optional arguments for
                :meth:`asdf.AsdfFile.write_to`. Defaults to {}.

        Raises:
            RuntimeError: If the current context state is
                :attr:`ContextState.staging`. This indicates a bug in the saving
                logic.
            RuntimeError: If the target directory could not be created.
            RuntimeError: If the asdf file already exists but
                ``overwrite=False``.
            RuntimeError: If a floating artifact, opened before
                :meth:`Experiment.save` was called, is not registered as an
                artifact in the collection. This indicates a bug in the
                :class:`FolderContext` logic.
            FileNotFoundError: If a floating artifact, opened before
                :meth:`Experiment.save` was called, cannot be found in the
                temporary directory.
            FileExistsError: If an artifact file already exists in the target
                directory but ``overwrite=False``.
            RuntimeError: If a bound artifact could not be saved.
            RuntimeError: If moving an artifact to the new target directory
                failed.
        """
        # Backup attributes that we may need to restore if we fail during staging.
        previous_state = self._state
        _original_artifacts_to_move = self._artifacts_to_move.copy()

        def _restore_state():
            """Temporary function to restore the context to before staging, in case of failure."""
            self._state = previous_state
            self._artifacts_to_move = _original_artifacts_to_move

        # *** Enter staging. Determine our target path. Raise if we are already in staging
        self._state = ContextState.staging
        if previous_state == ContextState.unsaved:
            # We are saving an unsaved context.
            # Therefore, self._current_path is a temporary directory and we need
            # to move artifacts in self._artifacts_to_move to the target
            # directory.
            target_path = target_path_for(experiment=experiment, root_dir=folder)
            logger.debug(
                "Entering staging. Setting target directory to %s", target_path.parent
            )
        elif previous_state == ContextState.saved:
            # We are saving a saved context. Therefore, self._current_dir is
            # the target directory. Do not recompute it as we may have
            # overwritten it with other code.
            target_path = self._current_path
            logger.debug(
                "Entering staging for already saved context. Target directory is %s",
                target_path.parent,
            )
        else:
            _restore_state()
            raise RuntimeError("Cannot save context already being saved.")

        # *** Make sure we have a target directory into which to save.
        try:
            # We don't check for the existence of this path as (1) files at the
            # given path exist and (2) mkdir will raise an error if the path
            # exists and is a file. If the path exists and is a folder, mkdir
            # does nothing as we set exist_ok=True.
            target_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error("Failed to create target directory %s", target_path.parent)

            # Revert to the previous state, so we don't mess up anything.
            _restore_state()

            # Raise an error
            raise RuntimeError(
                "Failed to create target directory for context save."
            ) from e

        if not overwrite and target_path.exists():
            _restore_state()
            raise RuntimeError("Target ASDF file already exists but overwrite=False.")

        # *** Validate that all already saved artifacts exist
        if previous_state == ContextState.unsaved:
            logger.debug(
                "Context was unsaved. Checking if artifacts to be moved exist."
            )
            for artifact_source in self._artifacts_to_move:
                # We double check if the artifact-to-move is also stored in
                # artifacts. This will raise an exception if the source doesn't
                # exist.
                try:
                    artifact = self.artifacts.get_for(source=artifact_source)
                except KeyError as e:
                    _restore_state()
                    raise RuntimeError(
                        "Artifact with source {!r} not found in collection of artifacts during move.".format(
                            artifact_source
                        )
                    ) from e

                # We use the source returned from the artifact info instance to
                # be sure we're using the correct one.
                artifact_path = self._current_path.parent.joinpath(artifact.source)

                # Check if the artifact exists in the temporary directory.
                if not artifact_path.exists():
                    _restore_state()
                    raise FileNotFoundError(
                        "Artifact {!r} (source={!r}) not found in temporary directory.".format(
                            artifact.name, artifact_path
                        )
                    )

        # *** Attempt save
        logger.debug("Attempting save of ASDF file to target directory.")
        logger.debug("Received the following asdf write_to kwargs:")
        for k, v in asdf_write_to_kwargs.items():
            logger.debug("\t{} = {}", k, v)

        # Get ASDF file
        tree: AsdfFile
        if not isinstance(experiment, AsdfFile):
            tree = experiment._tree
        else:
            tree = experiment

        # Extract values for tree and replace with artifacts.
        _bound_artifacts = self.artifacts.bound_artifacts()
        _extracted_values = replace_values_with_artifacts(
            tree=tree, artifacts=_bound_artifacts
        )
        tree["artifacts"] = self.artifacts

        def _restore_tree_artifacts():
            """Helper function to restore extracted values.

            Easier recovery when errors are raised. Also needed after saving
            as we want ``tree`` to still contain values for bound artifacts.
            """
            restore_values_for_artifacts(
                tree=tree, artifacts=_bound_artifacts, values=_extracted_values
            )
            del tree._tree["artifacts"]

        # If we aren't overwriting, we want to check if any artifacts already
        # exist. If they do, we fail.
        if not overwrite:
            for _bound_artifact in _bound_artifacts:
                if target_path.parent.joinpath(_bound_artifact.source).exists():
                    _restore_state()
                    _restore_tree_artifacts()
                    raise FileExistsError(
                        "Bound artifact attr={!r} "
                        "already exists in target folder but overwrite=False.".format(
                            _bound_artifact.attr
                        )
                    )
            for _artifact_source in self._artifacts_to_move:
                _artifact = self.artifacts.get_for(source=_artifact_source)
                if target_path.parent.joinpath(Path(_artifact.source)).exists():
                    _restore_state()
                    _restore_tree_artifacts()
                    raise FileExistsError(
                        "Floating artifact name={!r} already exists "
                        "in target folder but overwrite=False.".format(_artifact.name)
                    )

        # Write ASDF file to target path
        try:
            tree.write_to(target_path, **asdf_write_to_kwargs)
        except Exception as e:
            _restore_state()
            _restore_tree_artifacts()
            raise RuntimeError("Failed to write ASDF file to {}.", target_path) from e
        logger.info("ASDF file was saved to %s", target_path)

        # Save extracted artifacts
        for _artifact in _bound_artifacts:
            logger.info("Saving extracted bound artifact for attr=%r", _artifact.attr)
            _value = _extracted_values[_artifact.attr]
            _handler = handler_for(_artifact)
            _source = _artifact.source
            target_artifact_path = target_path.parent.joinpath(Path(_source))
            try:
                _handler.save_obj_to(_value, target_artifact_path)
            except Exception as e:
                _restore_tree_artifacts()
                _restore_state()
                raise RuntimeError(
                    "Failed to save bound artifact (attr={!r}).".format(_artifact.attr)
                ) from e
            logger.debug(
                "Saved bound artifact (attr=%r) with %s",
                _artifact.attr,
                _handler.__class__.__name__,
            )

        # Move artifacts if necessary. We actually copy them so we don't
        # lose the originals if an error occurs.
        if previous_state == ContextState.unsaved:
            logger.info(
                "Attempting move of %i artifacts as context was previously unsaved.",
                len(self._artifacts_to_move),
            )
            for _artifact_source in self._artifacts_to_move:
                artifact_info = self.artifacts.get_for(source=_artifact_source)
                # Check if the artifact exists in the previous directory.
                _artifact_path = self._current_path.parent.joinpath(
                    Path(artifact_info.source)
                )
                # Attempt copy
                _artifact_dst_path = target_path.parent.joinpath(
                    Path(artifact_info.source)
                )
                logger.info(
                    "Copying artifact %r with source %r to target folder.",
                    artifact_info.name,
                    artifact_info.source,
                )
                try:
                    _ = copy2(_artifact_path, _artifact_dst_path)
                except Exception as e:
                    _restore_tree_artifacts()
                    _restore_state()
                    raise RuntimeError(
                        "Failed to copy artifact (name={!r}) to new target directory.".format(
                            artifact_info.name
                        )
                    ) from e
        else:
            logger.info(
                "Not moving artifacts as they should already exist in the target directory.",
                "Previous state was not ContextState.unsaved.",
            )

        _restore_tree_artifacts()
        self._state = ContextState.saved
        self._current_path = target_path

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
        _is_new_artifact = False
        # Check that if such an artifact exists, that it isn't a bound artifact.
        if self.artifacts.exists_for(file=file, name=name):
            logger.info("Artifact with file and name already exists.")
            _artifact = self.artifacts.get_for(file=file, name=name)
            if _artifact.is_bound():
                logger.info(
                    "Artifact with file %r and name %r is a bound artifact.", file, name
                )
                raise RuntimeError("Cannot open bound artifact with open_artifact.")
            logger.info("Floating artifact found for file %r and name %r.", file, name)
        else:
            # Double check if we can add the given artifact.
            if file is not None and self.artifacts.exists_for(file=file, name=None):
                raise KeyError(
                    "An artifact with for that file already exists with a different name."
                )
            elif name is not None and self.artifacts.exists_for(file=None, name=name):
                raise KeyError(
                    "An artifact with that name already exists with a different source (file)."
                )
            elif file is None:
                # At this point, this is a new artifact. Those require a file.
                raise ValueError("file must be provided to open a new artifact.")
            _is_new_artifact = True
            _artifact = ArtifactInfo(
                file=file,
                name=name,
                description=description,
                format=None,
                floating=True,
            )

        # Get absolute path to artifact.
        if _is_new_artifact:
            logger.info("Adding new artifact {}", _artifact)
            self.artifacts._add_artifact(artifact=_artifact)
            self._artifacts_to_move.add(SourceStr(_artifact.source))
        artifact_path = self.get_artifact_path(artifact=_artifact)
        logger.info("ArtifactInfo path is '{}'.", artifact_path)
        return open(
            artifact_path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )

    def get_artifact_path(
        self,
        file: StrOrPath | None = None,
        source: str | None = None,
        name: str | None = None,
        artifact: ArtifactInfo | None = None,
    ) -> Path:
        """Get the path to an artifact.

        Args:
            file: Optional file of the artifact to retrieve. If provided,
                ``source`` and ``artifact`` cannot be provided. Defaults to None.
            source: Optional source of the artifact to retrieve. If provided,
                ``file`` and ``artifact`` cannot be provided. Defaults to None.
            name: Optional name of the artifact to retrieve. If provided,
                ``artifact`` cannot be provided. Defaults to None.
            artifact: Optional artifact whose path will be returned. The
                artifact's name and source are used to verify the artifact is
                part of this context. If None, ``file``, ``source``, and
                ``name`` are used. Defaults to None.

        Raises:
            ValueError: If ``artifact`` and at least one of ``name``,
                ``source``, and ``file`` are provided.

        Returns:
            A :class:`pathlib.Path` pointing to the artifact.
        """
        if artifact is not None:
            if file is not None or source is not None or name is not None:
                raise ValueError(
                    "file, source, and name must be None if artifact is provided."
                )
            source = artifact.source
            name = artifact.name
        _stored_artifact = self.artifacts.get_for(file=file, source=source, name=name)
        return self._current_path.parent.joinpath(Path(_stored_artifact.source))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, FolderContext):
            raise ValueError(
                "Cannot compare {} to {}.".format(self.__class__.__name__, type(value))
            )
        return (
            self._artifacts_to_move == value._artifacts_to_move
            and self.artifacts == value.artifacts
            and self._current_path == value._current_path
            and self._state == value.state
        )

    def __ne__(self, value: object, /) -> bool:
        if not isinstance(value, FolderContext):
            raise ValueError(
                "Cannot compare {} to {}.".format(self.__class__.__name__, type(value))
            )
        return (
            self._artifacts_to_move != value._artifacts_to_move
            or self.artifacts != value.artifacts
            or self._current_path != value._current_path
            or self._state != value.state
        )

    def __repr__(self) -> str:
        return "{}(state={}, current_path={})".format(
            self.__class__.__name__, self._state, self._current_path
        )


class FolderProvider(BaseProvider):
    @override
    def new_context(
        self,
    ) -> FolderContext:
        _context = FolderContext()
        return _context
