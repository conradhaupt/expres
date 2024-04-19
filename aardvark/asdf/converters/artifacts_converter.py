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

"""ArtifactInfo Converter"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asdf.extension import SerializationContext
    from aardvark.artifacts import ArtifactCollection, ArtifactInfo
    from aardvark.asdf.tags.artifact_info_tag import ArtifactInfoTag

from asdf.extension import Converter


class ArtifactConverter(Converter):
    """Converter for ArtifactInfo and collections of Artifacts.

    For floating artifacts, which exist under the ``"artifacts"`` entry in the
    ASDF file, we serialise them all together in an :class:`ArtifactCollection`.
    Note that artifact sources are relative POSIX paths. When converting to a
    YAML tree, Windows paths are converted to POSIX. When loading on Windows,
    paths are converted by :class:`ArtifactInfo` into a Windows Path.
    Additionally, saving artifact values is done by storage providers and not
    ASDF or ArtifactConverter.
    """

    tags = [
        # For collections
        "asdf://aardvark.org/asdf/tags/core/artifacts-0.0.0",
        # For single artifacts
        "asdf://aardvark.org/asdf/tags/core/artifact-0.0.0",
    ]
    """YAML tags for ArtifactsCollection types."""

    types = [
        "aardvark.artifacts.ArtifactCollection",
        "aardvark.artifacts.ArtifactInfo",
    ]
    """Types that are serialisable by :class:`ArtifactConverter`."""

    def _artifact_to_tree(self, artifact: ArtifactInfo) -> dict[str, Any]:
        from pathlib import PurePosixPath

        _tree = {
            "source": str(PurePosixPath(artifact._file)),
        }
        if artifact.description is not None:
            _tree["description"] = artifact.description
        if artifact.is_bound():
            if artifact.format is None:
                raise ValueError("Cannot serialise bound artifact without format.")
            _tree["format"] = artifact.format
        return _tree

    def select_tag(self, obj: "ArtifactInfo | ArtifactCollection", tags, ctx):
        from aardvark.artifacts import ArtifactInfo

        if isinstance(obj, ArtifactInfo):
            return "asdf://aardvark.org/asdf/tags/core/artifact-0.0.0"
        else:
            return "asdf://aardvark.org/asdf/tags/core/artifacts-0.0.0"

    def to_yaml_tree(
        self,
        obj: ArtifactCollection | ArtifactInfo,
        tag,
        ctx: SerializationContext,
    ):
        from aardvark.artifacts import ArtifactInfo, ArtifactCollection

        if isinstance(obj, ArtifactCollection):
            return {
                _a.name: self._artifact_to_tree(_a)
                for _a in obj._artifacts.values()
                if _a.is_floating()
            }
        elif isinstance(obj, ArtifactInfo):
            return self._artifact_to_tree(artifact=obj)
        raise RuntimeError(
            "{} cannot serialise {} into a YAML tree.".format(
                self.__class__.__name__, type(obj).__name__
            )
        )

    def from_yaml_tree(
        self, node, tag, ctx: SerializationContext
    ) -> ArtifactCollection | ArtifactInfoTag:
        from pathlib import PurePosixPath
        from aardvark.artifacts import ArtifactCollection, ArtifactInfo
        from aardvark.asdf.tags.artifact_info_tag import ArtifactInfoTag

        # For collections
        if tag == "asdf://aardvark.org/asdf/tags/core/artifacts-0.0.0":
            artifacts = ArtifactCollection()
            for _artifact_name, _artifact_tree in node.items():
                _description = _artifact_tree.get("description", None)
                _artifact = ArtifactInfo(
                    file=PurePosixPath(_artifact_tree["source"]),
                    name=str(_artifact_name),
                    description=str(_description) if _description is not None else None,
                    floating=True,
                )
                artifacts._add_artifact(artifact=_artifact)
            return artifacts
        # For single artifacts
        elif tag == "asdf://aardvark.org/asdf/tags/core/artifact-0.0.0":
            # We don't know the name of an artifact until it's in the tree, so
            # we return an ArtifactInfoTag instead of an ArtifactInto.
            return ArtifactInfoTag(
                source=node["source"],
                description=node.get("description", None),
                floating=False,
                format=node["format"],
            )
        else:
            raise NotImplementedError(
                "{} cannot deserialise tag {!r}.".format(self.__class__.__name__, tag)
            )
