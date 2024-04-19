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
from typing import TYPE_CHECKING, TypeVar

from asdf import AsdfFile

import aardvark.experiment
from aardvark.artifacts.handlers.utils import bound_artifact_for
from aardvark.dataclasses import MISSING, Field
from aardvark.storage.base_provider import BaseContext

# if TYPE_CHECKING:
E = TypeVar("E", bound="aardvark.experiment.Experiment")


def register_cls_bound_artifacts_with_context(
    cls: type[E],
    context: BaseContext,
):
    """Register bound artifacts in ``cls`` with the given context.

    Args:
        cls: A subclass of :class:`Experiment`.
        context: A :class:`BaseContext` instance, such as
            :class:`FolderContext`.

    Raises:
        RuntimeError: If a bound artifact is found but the context already
        thinks it's a floating artifact.
    """
    # Register bound artifacts from class definition.
    for _bound_attr, _bound_metadata in cls._class_artifact_metadata().items():
        # Double check if context already has this artifact stored. If yes,
        # we must assume the ASDF file has already processed this artifact.
        if context.artifacts.exists_for(name=_bound_attr):
            _artifact = context.artifacts.get_for(name=_bound_attr)
            if _artifact.is_floating():
                raise RuntimeError(
                    "{} artifact {!r} is bound but context says it's floating.".format(
                        cls.__name__, _bound_attr
                    )
                )
            continue

        # Artifact is not in context, so we add it.
        _artifact = bound_artifact_for(
            attr_name=_bound_attr, artifact_metadata=_bound_metadata
        )
        context.artifacts._add_artifact(artifact=_artifact)


def populate_default_attrs_if_nonexistent(
    cls: type[E],
    tree: AsdfFile,
    warn: bool = True,
):
    """Populates ``tree`` with defaults from the :class:`Experiment` class
       definition ``cls``.

    Args:
        cls: Subclass of :class:`Experiment`, defining fields/attributes and
            defaults.
        tree: ASDF tree to assign default values for attributes that exist in
            ``cls`` but not in ``tree``.
        warn: Whether to warn about attributes in ``cls`` that are not in
            ``tree``, but have no defaults. Defaults to True.
    """
    for _attr in cls._class_tree_attrs():
        # Check if the given attribute exists in the tree
        if _attr not in tree:
            # Check if we have a default value.
            field: Field = cls.__dataclass_fields__[_attr]
            if field.default != MISSING:
                # We have a default value
                if warn:
                    warnings.warn(
                        "Attribute {!r} does not exist in ASDF tree. Setting to default {!r}.".format(
                            _attr, field.default
                        ),
                    )
                tree[_attr] = field.default
            elif field.default_factory != MISSING:
                _new_value = field.default_factory()
                if warn:
                    warnings.warn(
                        "Attribute {!r} does not exist in ASDF tree. Setting to result from default_factory(): {!r}.".format(
                            _attr, _new_value
                        )
                    )
                tree[_attr] = _new_value
            else:
                if warn:
                    warnings.warn(
                        "Attribute {!r} has no default or default_factory in {}, and isn't in ASDF tree. Leaving unassigned.".format(
                            _attr, cls.__name__
                        ),
                        RuntimeWarning,
                    )
