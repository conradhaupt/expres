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

from pathlib import Path, PurePath

from aardvark.utils.io import StrOrPath_to_Path
from aardvark.utils.io.typeshed import StrOrPath

from .typing import NameStr, SourceStr


def norm_source(source: str) -> SourceStr:
    """Convert a source string to a :type:`SourceStr`.

    Useful for ensuring type checkers treat parsed source strings differently to strings.
    """
    return SourceStr(str(Path(source)))


def norm_name(name: str) -> NameStr:
    """Convert a name string to a :type:`NameStr`.

    Useful for ensuring type checkers treat parsed name strings differently to strings.
    """
    return NameStr(name)


def file_to_path(file: StrOrPath | PurePath) -> Path:
    """Helper function for converting ``file`` into an appropriate :class:`pathlib.Path` instance."""
    return StrOrPath_to_Path(file)


def path_to_source(file: PurePath) -> str:
    """Helper function for converting ``file`` into an appropriate source string."""
    return str(file)


def file_to_source(file: StrOrPath | PurePath) -> str:
    """Helper function for converting a file to a source string."""
    return path_to_source(file_to_path(file))
