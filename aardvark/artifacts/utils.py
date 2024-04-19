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

from collections.abc import Iterable
from typing import Any

import asdf

from aardvark.artifacts.artifact import ArtifactInfo
from aardvark.asdf.tags import ArtifactInfoTag


def artifacts_from_asdf(tree: asdf.AsdfFile) -> list[ArtifactInfo]:
    """Return a list of ArtifactInfo instances matching artifacts in the first level of an ASDF tree.

    Args:
        tree: The tree from which the artifacts should be extracted.

    Raises:
        ValueError: If an :class:`ArtifactInfo` instance is encountered whose
            ``name`` does not match the attribute key in ``tree``.
        ValueError: If a floating :class:`ArtifactInfo` instance is encountered,
            as these should only exist inside an :class:`ArtifactCollection`.
        ValueError: If an :class:`ArtifactInfoTag` instance is encountered whose
            ``name`` does not match the attribute key in ``tree``.

    Returns:
        A list of artifact infos for the ASDF tree.
    """
    artifact_infos: list[ArtifactInfo] = []
    for k in tree.keys():
        val = tree[k]
        if isinstance(val, ArtifactInfo):
            # Double check that the artifact info instance matches the attribute name.
            if val.is_bound() and val.attr != k:
                raise ValueError(
                    "ArtifactInfo for entry {!r} has the wrong name: got {!r} instead.".format(
                        k, val.attr
                    )
                )
            elif val.is_floating():
                raise ValueError(
                    "ASDF files should not contain floating ArtifactInfo instances. These should be in an ArtifactCollection."
                )
            artifact_infos.append(val)
        elif isinstance(val, ArtifactInfoTag):
            if val.name is not None and val.name != k:
                raise ValueError(
                    "Encountered ArtifactInfoTag with name {!r} that does not match attribute {!r}.".format(
                        val.name, k
                    )
                )
            artifact_info = val.to_artifact_info(name=k)
            artifact_infos.append(artifact_info)
    return artifact_infos


def replace_values_with_artifacts(
    tree: asdf.AsdfFile, artifacts: Iterable[ArtifactInfo]
) -> dict[str, Any]:
    """Replace values in ``tree`` with artifacts, returning values that were
       removed.

       Note that ``tree`` is modified in-place.

    Args:
        tree: The tree to be updated, from which values are extracted in-place.
        artifacts: Artifacts that should be inserted into ``tree``, using
            :attr:`ArtifactInfo.attr`.

    Raises:
        ValueError: If multiple artifacts have the same attribute name.
        KeyError: If an artifact attribute cannot be found in ``tree``.

    Returns:
        Returns the extracted values as a mapping where keys are attribute
        names.
    """
    _extracted_values: dict[str, Any] = {}

    def _restore_state():
        for _attr, _val in _extracted_values.items():
            tree[_attr] = _val

    for _artifact_info in artifacts:
        if _artifact_info.attr in _extracted_values:
            _restore_state()
            raise ValueError(
                "Cannot replace multiple artifacts with name {!r}.".format(
                    _artifact_info.attr
                )
            )
        if _artifact_info.attr not in tree:
            _restore_state()
            raise KeyError(
                "Artifact attr {!r} not found in ASDF tree.".format(_artifact_info.attr)
            )
        _extracted_values[_artifact_info.attr] = tree[_artifact_info.attr]
        tree[_artifact_info.attr] = _artifact_info

    return _extracted_values


def restore_values_for_artifacts(
    tree: asdf.AsdfFile, artifacts: Iterable[ArtifactInfo], values: dict[str, Any]
):
    """Restore values in ``tree`` from ``values``, based on artifact info in ``artifacts``.

    Args:
        tree: The tree to be modified. Note that ``tree`` is modified in-place.
        artifacts: The list of artifacts to restore.
        values: The collection of values to be restored, where keys are
            :attr:`ArtifactInfo.attr`. Note that ``values`` is modified in-place
            values that are restored are removed.

    Raises:
        ValueError: If there are multiple artifacts in ``artifacts`` with the
            same :attr:`ArtifactInfo.attr` value.
        KeyError: If an artifact attribute does not exist in the tree.
        KeyError: If a value for an artifact does not exist in ``values``.
    """
    _removed_values: dict[str, Any] = {}

    def _restore_artifacts():
        for _attr, _artifact_info in _removed_values.items():
            _val = tree[_artifact_info.attr]
            values[_artifact_info.attr] = _val
            tree[_artifact_info.attr] = _artifact_info

    for _artifact_info in artifacts:
        if _artifact_info.attr in _removed_values:
            _restore_artifacts()
            raise ValueError(
                "Cannot remove multiple artifacts with name {!r}.".format(
                    _artifact_info.attr
                )
            )
        if _artifact_info.attr not in tree:
            _restore_artifacts()
            raise KeyError(
                "Artifact attr {!r} not found in ASDF tree.".format(_artifact_info.attr)
            )
        if _artifact_info.attr not in values:
            _restore_artifacts()
            raise KeyError(
                "No value for artifact name {!r} in values.".format(_artifact_info.attr)
            )
        _removed_values[_artifact_info.attr] = tree[_artifact_info.attr]
        _value = values.pop(_artifact_info.attr)
        tree[_artifact_info.attr] = _value
