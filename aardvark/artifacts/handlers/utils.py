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

from typing import Any

from aardvark.artifacts import ArtifactInfo
from aardvark.artifacts.typing import ArtifactFormat

from .base_artifact_handler import BaseArtifactHandler
from .ndarray_artifact_handler import NDArrayArtifactHandler

HANDLER_FORMAT_MAPPING: dict[ArtifactFormat, type[BaseArtifactHandler]] = {
    "npz": NDArrayArtifactHandler
}


def bound_artifact_for(
    attr_name: str, artifact_metadata: dict[str, Any]
) -> ArtifactInfo:
    """Create a bound artifact as an :class:`ArtifactInfo` instance based on an
       attribute name and the :meth:`~aardvark.dataclasses.artifact` metadata.

    Args:
        attr_name: The name of the Experiment attribute or ASDF tree key.
        artifact_metadata: Metadata for the artifact. Must include ``"format"``
            (:type:`ArtifactFormat`). Other optional keys are ``"source"`` and
            ``"description"``.

    Raises:
        ValueError: If ``artifact_metadata`` does not have a valid ``"format"`` entry.

    Returns:
        The bound artifact as an instance of :class:`ArtifactInfo` for the given
        attribute.
    """
    format = str(artifact_metadata["format"])
    if format not in HANDLER_FORMAT_MAPPING:
        raise ValueError("Format {!r} does not have a handler.".format(format))
    handler_cls = HANDLER_FORMAT_MAPPING[format]
    if artifact_metadata.get("source", None) is None:
        source = handler_cls.source_for(attr=attr_name)
    else:
        source = str(artifact_metadata["source"])
    return ArtifactInfo(
        file=source,
        name=attr_name,
        description=artifact_metadata.get("description", None),
        format=format,
        floating=False,
    )


def handler_for(artifact: ArtifactInfo) -> BaseArtifactHandler:
    """Create and return an artifact handler for the given artifact.

    Args:
        artifact: The artifact for which the handler should be created.

    Raises:
        ValueError: If :attr:`ArtifactInfo.format` is None.
        NotImplementedError: If no handler is defined for the given format.

    Returns:
        An instance of the appropriate :class:`BaseArtifactHandler` subclass,
        for ``artifact``.
    """
    if artifact.format is None:
        raise ValueError("Cannot get handler for artifact without a format.")
    if artifact.format not in HANDLER_FORMAT_MAPPING:
        raise NotImplementedError(
            "Handler for format {!r} not implemented.".format(artifact.format)
        )
    handler_cls = HANDLER_FORMAT_MAPPING[artifact.format]
    handler = handler_cls()
    return handler
