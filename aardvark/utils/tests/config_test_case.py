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

import tempfile
from collections.abc import Callable
from os.path import join as path_join
from typing import Any

from aardvark.utils.tests import TestCase


def _callable_for_tempfile(file_content: str) -> Callable[[], str]:
    """Create a callable that returns a path to a temporary file with the given content.
    Args:
        file_content: The content of the temporary file.

    Returns:
        A callable with signature ``function()`` whre the returned value is a
        path to a temporary file with contents ``file_content``.
    """

    def _closure(*args, **kwargs) -> str:
        _fd, _filename = tempfile.mkstemp()
        with open(_fd, "w") as f:
            f.write(file_content)
        return _filename

    return _closure


def _callable_for_nonexistent_file() -> Callable[[str], str] | Callable[[], str]:
    """Create a callable that returns a path to a nonexistent file in a
       temporary folder that does exist.

    Returns:
        A callable with signature ``function(*args,**kwargs)`` where arguments
        are ignored.
    """

    def _closure(*args, **kwargs) -> str:
        return path_join(tempfile.mkstemp()[1], "nonexistent_file.yml")

    return _closure


def _callable_for_multiple_tempfiles(**kwargs: str) -> Callable[[str], str]:
    """Create a callable that returns a path to a temporary file, indexed by a
    key, with the given content.

    Args:
        kwargs: File contents where the key is the argument to the returned
            callable, and the value is the contents of the file pointed to by
            the returned callable.

    Returns:
        A callable with signature ``function(dir:str)`` where ``dir`` is the
        key in ``kwargs`` and the returned value is a path to a temporary file
        with contents ``kwargs[dir]``.
    """

    def _closure(dir: str) -> str:
        _fd, _filename = tempfile.mkstemp()
        with open(_fd, "w") as f:
            f.write(kwargs[dir])
        return _filename

    return _closure


def patch_multiple_configs(
    global_config_yaml: str | None = None,
    local_config_yaml: str | dict[str, str] | None = None,
) -> dict[str, Any]:
    """Arguments to mock the available global and local configs.

    Args:
        global_config_yaml: Optional global config YAML. Defaults to None.
        local_config_yaml: Optional local config YAML files. If a string, then
            this is the local config for all local directories. If a dictionary,
            then the key is the relative directory and the value is the local
            config YAML. Defaults to None.

    Returns:
        Arguments appropriate for :attr:`~unittest.mock.patch.multiple` with
        :class:`ConfigTestCase`.
    """

    _patch_multiple_kwargs: dict[str, Any] = {}
    if global_config_yaml is not None:
        _patch_multiple_kwargs["global_config_path"] = _callable_for_tempfile(
            global_config_yaml
        )
    else:
        # If we haven't defined a global config, we create a temporary filename
        # but don't create the file. This would return False for .exists().
        _patch_multiple_kwargs["global_config_path"] = _callable_for_nonexistent_file()
    if local_config_yaml is not None:
        if isinstance(local_config_yaml, dict):
            _patch_multiple_kwargs["local_config_path"] = (
                _callable_for_multiple_tempfiles(**local_config_yaml)
            )
        else:
            _patch_multiple_kwargs["local_config_path"] = _callable_for_tempfile(
                local_config_yaml
            )
    else:
        # If we haven't defined a local config, we create a temporary filename
        # but don't create the file. This would return False for .exists().
        _patch_multiple_kwargs["local_config_path"] = _callable_for_nonexistent_file()
    return _patch_multiple_kwargs


class MockConfigTestCase(TestCase):
    """UnitTest testcase that provides a clean :class:`Config`."""

    def setUp(self) -> None:
        from aardvark.config.config import _config_context

        if hasattr(_config_context, "config"):
            delattr(_config_context, "config")

    def tearDown(self) -> None:
        from aardvark.config.config import _config_context

        if hasattr(_config_context, "config"):
            delattr(_config_context, "config")
