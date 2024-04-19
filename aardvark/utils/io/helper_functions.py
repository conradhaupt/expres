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

from pathlib import Path, PurePath, PurePosixPath
from .typeshed import StrOrPath, PathLike
from os.path import basename

# We cannot use os.path.sep as this is specific to the current OS. We must
# support running experiments on different platforms. Currently the only path
# separators are forward- and back-slashes, i.e., Windows and POSIX.
SEPS = ["\\", "/"]
"""List of possible separators for paths."""


def StrOrPath_to_Path(path: StrOrPath) -> Path:  # type: ignore
    """Convert :type:`StrOrPath` to a system Path.

    Paths can be strings or :class:`PathLike`. :mod:`aardvark` handles paths as
    :class:`~pathlib.PurePath` objects, so we need to convert them to the
    correct format. This method does that, assuming that :type:`bytes` use utf-8
    encoding. If ``path`` is an instance of :class:`~pathlib.PurePath`, then it
    is converted to :class:`~pathlib.Path` directly. If not, then it is
    converted to a string with ``__fspath__()`` first and then a
    :class:`~pathlib.Path` instance is created.

    Raises:
        ValueError: If the path is not :type:`StrOrPath`.
    """
    # Convert to the system-native Path
    if isinstance(path, PurePath):
        return Path(path)
    # __fspath__ returns str or bytes for PathLike.
    if isinstance(path, PathLike):
        path = path.__fspath__()  # type: ignore
    # We assume
    if isinstance(path, bytes):
        path = str(path, encoding="utf-8")
    return Path(path)


def could_be_file_path(path: str) -> bool:
    """If ``path`` could refer to a file.

    This actually checks if the path refers to a folder, based on the suffix.
    Note that ``path`` is converted to a string with
    :class:`~pathlib.PurePosixPath`, with ``str(PurePosixPath(path))``, before
    string parsing. For example, ``./data/`` cannot refer to a file as it has a
    trailing folder separator. Additionally, ``./data/..`` refers to a parent
    folder.

    Args:
        path: The path to check.

    Returns:
        If ``path`` could possibly refer to a file.
    """
    if len(path) == 0:
        return False
    if any(path.endswith(_sep) for _sep in SEPS):
        return False
    if basename(path).endswith("."):
        return False
    return True
