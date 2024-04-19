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

import dataclasses as dc
from typing import Protocol, TypeAlias

# from aardvark.artifacts.typing import ArtifactFormat
ArtifactFormat: TypeAlias = str

dataclass = dc.dataclass
MISSING = dc.MISSING
Field = dc.Field
field = dc.field
is_dataclass = dc.is_dataclass


def artifact(
    format: ArtifactFormat,
    source: str | None = None,
    description: str | None = None,
    default=MISSING,
    default_factory=MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    metadata=None,
    kw_only=MISSING,
):
    _metadata = {
        "artifact_info": {
            "format": format,
            "source": source,
            "description": description,
        }
    }
    if metadata is not None:
        _metadata.update(metadata)
    return field(
        default=default,
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata=_metadata,
        kw_only=kw_only,
    )


# *** Typing definitions for dataclasses
class Dataclass(Protocol):
    """A protocol for Dataclass type hints."""

    __dataclass_fields__: dict[str, dc.Field]
    # Ignore _DataclassParams not being found, as it's a private class.
    __dataclass_params__: dc._DataclassParams  # type: ignore
