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
import enum
import sys
from collections import Mapping
from collections.abc import Callable
from typing import Any, Literal, TypeVar, overload

from aardvark.artifacts.typing import ArtifactFormat

dataclass = dc.dataclass
MISSING = dc.MISSING
Field = dc.Field
field = dc.field
replace = dc.replace
is_dataclass = dc.is_dataclass

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)

# define _MISSING_TYPE as an enum within the type stubs,
# even though that is not really its type at runtime
# this allows us to use Literal[_MISSING_TYPE.MISSING]
# for background, see:
#   https://github.com/python/typeshed/pull/5900#issuecomment-895513797
class _MISSING_TYPE(enum.Enum):
    MISSING = enum.auto()

if sys.version_info >= (3, 14):
    @overload  # `default` and `default_factory` are optional and mutually exclusive.
    def artifact(
        *,
        format: ArtifactFormat,
        default: _T,
        default_factory: Literal[_MISSING_TYPE.MISSING] = ...,
        init: bool = True,
        repr: bool = True,
        hash: bool | None = None,
        compare: bool = True,
        metadata: Mapping[Any, Any] | None = None,
        kw_only: bool | Literal[_MISSING_TYPE.MISSING] = ...,
        doc: str | None = None,
    ) -> _T: ...
    @overload
    def artifact(
        *,
        format: ArtifactFormat,
        default: Literal[_MISSING_TYPE.MISSING] = ...,
        default_factory: Callable[[], _T],
        init: bool = True,
        repr: bool = True,
        hash: bool | None = None,
        compare: bool = True,
        metadata: Mapping[Any, Any] | None = None,
        kw_only: bool | Literal[_MISSING_TYPE.MISSING] = ...,
        doc: str | None = None,
    ) -> _T: ...
    @overload
    def artifact(
        *,
        format: ArtifactFormat,
        default: Literal[_MISSING_TYPE.MISSING] = ...,
        default_factory: Literal[_MISSING_TYPE.MISSING] = ...,
        init: bool = True,
        repr: bool = True,
        hash: bool | None = None,
        compare: bool = True,
        metadata: Mapping[Any, Any] | None = None,
        kw_only: bool | Literal[_MISSING_TYPE.MISSING] = ...,
        doc: str | None = None,
    ) -> Any: ...

else:
    #  sys.version_info >= (3, 10) but we only support >=3.10, so this is the default.

    @overload  # `default` and `default_factory` are optional and mutually exclusive.
    def artifact(
        *,
        format: ArtifactFormat,
        default: _T,
        default_factory: Literal[_MISSING_TYPE.MISSING] = ...,
        init: bool = True,
        repr: bool = True,
        hash: bool | None = None,
        compare: bool = True,
        metadata: Mapping[Any, Any] | None = None,
        kw_only: bool | Literal[_MISSING_TYPE.MISSING] = ...,
    ) -> _T: ...
    @overload
    def artifact(
        *,
        format: ArtifactFormat,
        default: Literal[_MISSING_TYPE.MISSING] = ...,
        default_factory: Callable[[], _T],
        init: bool = True,
        repr: bool = True,
        hash: bool | None = None,
        compare: bool = True,
        metadata: Mapping[Any, Any] | None = None,
        kw_only: bool | Literal[_MISSING_TYPE.MISSING] = ...,
    ) -> _T: ...
    @overload
    def artifact(
        *,
        format: ArtifactFormat,
        default: Literal[_MISSING_TYPE.MISSING] = ...,
        default_factory: Literal[_MISSING_TYPE.MISSING] = ...,
        init: bool = True,
        repr: bool = True,
        hash: bool | None = None,
        compare: bool = True,
        metadata: Mapping[Any, Any] | None = None,
        kw_only: bool | Literal[_MISSING_TYPE.MISSING] = ...,
    ) -> Any: ...
