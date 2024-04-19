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

"""Configuration for Aardvark that is saved to a YAML file."""

import json
import pkgutil
import threading
from collections.abc import Generator
from contextlib import contextmanager
from os.path import abspath, curdir, exists, expanduser, join
from pathlib import Path
from typing import Any, TypedDict

import yaml
from jsonschema import ValidationError, validate

from aardvark.utils.containers import NestedChainMap

try:
    from typing import Self
except:
    from typing_extensions import Self


class Config_FolderStorageProvider(TypedDict):
    """Type hint for :class:`~aardvark.storage.folder_provider.FolderProvider` config."""

    root_dir: str
    """The root directory for saved experiments."""

    temp_dir: str | None
    """The directory where unsaved experiments are stored.

    If this is a relative path, it will be relative to the current working
    directory during program execution. If None, then the system's temporary
    file location will be used.
    """

    folder_format: str
    """Python format string for single experiment folder names.

    This supports including experiment attributes. For more information, see
    :class:`~aardvark.storage.folder_provider.FolderProvider`."""
    filename_format: str
    """Python format string for experiment ASDF filenames.

    This supports including experiment attributes. For more information, see
    :class:`~aardvark.storage.folder_provider.FolderProvider`."""

    description_max_length: int
    """Maximum number of characters from the description to include in folder
       and file names.

    Defaults to ``15``."""


class Config_StorageProviders(TypedDict):
    """Type hint for provider configs."""

    folder_storage_provider: Config_FolderStorageProvider
    """Config for :class:`~aardvark.storage.folder_provider.FolderProvider`."""


class Config(TypedDict):
    """Type hint for config file."""

    config_version: str
    """Version number for config structure."""
    storage_providers: Config_StorageProviders
    """Provider configs."""


class ConfigClass(NestedChainMap):
    def __enter__(self) -> Self:
        return self.new_child({})

    def __exit__(self):
        pass


CURRENT_CONFIG_VERSION = "0.1.0"
"""Config version to handle changes to config files in future version."""

CONFIG_FILENAME = ".aardvark.yml"
"""Name of config files."""

if (
    _schema_bytes := pkgutil.get_data(
        package="aardvark",
        resource="resources/schemas/config-{}.json".format(CURRENT_CONFIG_VERSION),
    )
) is None:
    raise RuntimeError("Cannot load config schema.")
else:
    _schema_str = _schema_bytes.decode("utf8")

SCHEMA = json.loads(_schema_str)
"""Parsed JSON schema for config files."""


def cwd() -> Path:
    return Path.cwd()


def global_config_path() -> Path:
    """Path to global config file, regardless of if it exists or not.

    Returns:
        The absolute path to the global config file.
    """
    return Path("~").joinpath(Path(CONFIG_FILENAME)).expanduser().absolute()


def local_config_path(dir: str | Path | None = None) -> Path:
    """Path to local config file regardless of if it exists or not.

    Args:
        dir: Optional local directory for the local config file. If None, the
        current working directory is used. Defaults to None.

    Returns:
        The absolute path to the local config file.
    """
    if dir is None:
        _dir = cwd()
    else:
        _dir = Path(dir)
    return _dir.joinpath(CONFIG_FILENAME).absolute()


def default_config() -> Config:
    """The default config file, used when a global config file doesn't exist."""
    return {
        "config_version": CURRENT_CONFIG_VERSION,
        "storage_providers": {
            "folder_storage_provider": {
                "root_dir": ".",
                "temp_dir": None,
                "filename_format": "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}.asdf",
                "folder_format": "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}",
                "description_max_length": 15,
            }
        },
    }


def global_config() -> Config | None:
    _path = global_config_path()
    try:
        if not exists(_path):
            return None
        with open(_path, "r") as f:
            _config = yaml.load(f, Loader=yaml.SafeLoader)
        validate(_config, SCHEMA)
        return _config
    except ValidationError as e:
        raise RuntimeError("Global config failed validation.") from e
    except Exception as e:
        raise RuntimeError("Failed to load global config '{}'.".format(_path)) from e


def local_config_for(dir: str | Path) -> dict[str, Any | dict] | None:
    _path = local_config_path(dir=dir)
    try:
        if not exists(_path):
            return None
        with open(_path, "r") as f:
            _config = yaml.load(f, Loader=yaml.SafeLoader)
        validate(_config, SCHEMA)
        return _config
    except ValidationError as e:
        raise RuntimeError(
            "Local config failed validation: dir='{}', path={}".format(dir, _path)
        ) from e
    except Exception as e:
        raise RuntimeError("Failed to load local config '{}'.".format(_path)) from e


def __must_init_config_context() -> bool:
    """Returns whether ``__init_config_context`` must be reinitialise the
    current config."""
    return not hasattr(_config_context, "config")


def __init_config_context():
    if __must_init_config_context():
        config = NestedChainMap(default_config())
        _global = global_config()
        if _global is not None:
            config = config.new_child(_global)
        _local = local_config_for(cwd())
        if _local is not None:
            config = config.new_child(_local)

        # We always include an empty config with the highest precedence. This
        # way we never lose the loaded config values.
        config = config.new_child({})
        # Validate doesn't work on NestedChainMap, so we convert to a nested
        # dictionary.
        validate(config.__dict__(), SCHEMA)
        _config_context.config = config


def get_config() -> Config:
    """Get the current Aardvark config."""
    # We ignore type checking here. Even though we're returning a
    # NestedChainMap, we want users to "see" a Config.

    __init_config_context()
    return _config_context.config


@contextmanager
def temp_config() -> Generator[Config]:
    """Get a new config, inheriting the current config, in a context manager."""
    # We ignore type checking here. Even though we're returning a
    # NestedChainMap, we want users to "see" a Config.

    __init_config_context()
    _old_config = _config_context.config
    _config_context.config = _old_config.new_child({})
    yield _config_context.config
    _config_context.config = _old_config


_config_context = threading.local()
"""Thread context for the current config."""
