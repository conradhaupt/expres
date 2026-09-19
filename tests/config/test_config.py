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

import unittest.mock as mock
from os.path import join
from pathlib import Path

# Import the config module so mocking works, instead of importing functions from
# the module.
import aardvark.config.config as config
import yaml
from aardvark.utils.containers import NestedChainMap
from aardvark.utils.tests.config_test_case import (
    MockConfigTestCase,
    patch_multiple_configs,
)


def DUMMY_GLOBAL_CONFIG_YAML(dir: str) -> str:
    """Create and return the content of a global YAML config file.


    Args:
        dir: The folder for the root directory, inside ``/home/user/``. This is
            useful to confirm that a test is loading the correct version of this
            global config.
    """
    return (
        """# This part of the config file should not be changed by users. When a config
# file is loaded by aardvark, it should automatically be updated and saved in
# newer versions.
config_version: 0.1.0

# Aardvark will support multiple ways of saving experiments. The only provider
# right now is FolderProvider, which saves experiment instances in their own
# folder, alongside artifacts.
storage_providers:
  # FolderProvider configuration values.
  folder_storage_provider:
    # Root directory for all experiments.
    root_dir: "/home/user/{dir}" """.format(dir=dir)
        + """
    # Python format string for the ASDF filename.
    filename_format: "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}.asdf"
    # Python format string for the experiment folder, in which the ASDF file and
    # artifacts will be saved.
    folder_format: "{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
    # Number of characters in {desc}
    description_max_length: 25
"""
    )


def DUMMY_LOCAL_CONFIG_YAML(prefix: str) -> str:
    return (
        """
storage_providers:
    folder_storage_provider:
        folder_format: "{prefix}""".format(prefix=prefix)
        + """_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
"""
    )


def DUMMY_LOCAL_CONFIG_YAML_PARAM(prefix: str) -> str:
    return (
        """
    storage_providers:
      folder_storage_provider:
        folder_format: \""""
        + prefix
        + """_{experiment_name}_{date_created:%Y%m%d_%H%M}{desc}_{uuid_short}"
    """
    )


class TestConfigLoading(MockConfigTestCase):
    """Test loading of global and local configs, with mocked YAML files."""

    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            global_config_yaml=DUMMY_GLOBAL_CONFIG_YAML("test_global_config")
        ),
    )
    def test_global_config(self):
        """Test that the global config is correct."""
        _global = config.global_config()
        self.assertIsNotNone(_global, "Global config should exist.")
        _expected = yaml.load(
            DUMMY_GLOBAL_CONFIG_YAML("test_global_config"), Loader=yaml.SafeLoader
        )
        self.assertDictEqual(
            _global,
            _expected,
        )

    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            local_config_yaml=DUMMY_LOCAL_CONFIG_YAML(prefix="test_local_config")
        ),
    )
    def test_local_config(self):
        """Test that the local config is correct."""
        _local = config.local_config_for(None)
        _expected = yaml.load(
            DUMMY_LOCAL_CONFIG_YAML(prefix="test_local_config"), Loader=yaml.SafeLoader
        )
        self.assertEqual(_expected, _local)

    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            global_config_yaml=DUMMY_GLOBAL_CONFIG_YAML("test_local_override"),
            local_config_yaml=DUMMY_LOCAL_CONFIG_YAML("test_local_override"),
        ),
    )
    def test_local_override(self):
        """Test that both global and local configs are merged correctly."""
        _config = config.get_config()
        _expected_default = config.default_config()
        _expected_global = yaml.load(
            DUMMY_GLOBAL_CONFIG_YAML("test_local_override"),
            Loader=yaml.SafeLoader,
        )
        _expected_local = yaml.load(
            DUMMY_LOCAL_CONFIG_YAML("test_local_override"),
            Loader=yaml.SafeLoader,
        )
        _expected = NestedChainMap(
            _expected_default, _expected_global, _expected_local
        ).__dict__()
        self.assertEquivalentNestedChainMap(_config, _expected)

    @mock.patch.multiple(
        "aardvark.config.config",
        **patch_multiple_configs(
            global_config_yaml=DUMMY_GLOBAL_CONFIG_YAML(
                "test_different_local_overrides"
            ),
            local_config_yaml={
                "folder1": DUMMY_LOCAL_CONFIG_YAML_PARAM("folder1"),
                "folder2": DUMMY_LOCAL_CONFIG_YAML_PARAM("folder2"),
            },
        ),
    )
    def test_different_local_overrides(self):
        """Test that local configs correct when in a different working directory."""
        from aardvark.config.config import _config_context

        # Reset the config in _config_context just to be sure we load the
        # correct ones from the cwd.MockConfigTestCase
        _old_config = getattr(_config_context, "config", None)
        if hasattr(_config_context, "config"):
            delattr(_config_context, "config")
        with mock.patch("aardvark.config.config.cwd", new=lambda: "folder1") as _mock:
            _config_folder1 = config.get_config()
        if hasattr(_config_context, "config"):
            delattr(_config_context, "config")
        with mock.patch("aardvark.config.config.cwd", new=lambda: "folder2") as _mock:
            _config_folder2 = config.get_config()
        if _old_config is not None:
            _config_context.config = _old_config

        _default = config.default_config()
        _global = yaml.load(
            DUMMY_GLOBAL_CONFIG_YAML("test_different_local_overrides"),
            Loader=yaml.SafeLoader,
        )
        _local_folder1 = yaml.load(
            DUMMY_LOCAL_CONFIG_YAML_PARAM("folder1"), Loader=yaml.SafeLoader
        )
        _local_folder2 = yaml.load(
            DUMMY_LOCAL_CONFIG_YAML_PARAM("folder2"), Loader=yaml.SafeLoader
        )
        _expected_folder1 = NestedChainMap(_default, _global, _local_folder1).__dict__()
        _expected_folder2 = NestedChainMap(_default, _global, _local_folder2).__dict__()
        self.assertEquivalentNestedChainMap(_config_folder1, _expected_folder1)
        self.assertEquivalentNestedChainMap(_config_folder2, _expected_folder2)


# Make sure global and local configs are not set.
@mock.patch.multiple(
    "aardvark.config.config",
    **patch_multiple_configs(global_config_yaml=None, local_config_yaml=None),
)
class TestConfigWithoutLoading(MockConfigTestCase):
    """Test functionality of Config, excluding loading functionality."""

    def test_mocking_works(self):
        """Test that we correctly mock the paths to the global and local configs."""
        _global_path = Path(config.global_config_path())
        self.assertFalse(
            _global_path.exists(),
            "Global config path should not exist for {}: {}".format(
                self.__class__.__name__, _global_path
            ),
        )
        self.assertIn(
            "nonexistent_file.yml",
            str(_global_path),
            "Global config path should be a nonexistent yml file.",
        )
        _local_path = Path(config.local_config_path())
        self.assertFalse(
            _local_path.exists(),
            "Local config path should not exist for {}: {}".format(
                self.__class__.__name__, _local_path
            ),
        )
        self.assertIn(
            "nonexistent_file.yml",
            str(_local_path),
            "Local config path should be a nonexistent yml file.",
        )

    def test_current_config_is_default(self):
        """Test the global_config_path and local_config_path were called."""
        _actual_default = config.get_config()
        _expected = config.default_config()
        self.assertEquivalentNestedChainMap(_actual_default, _expected)

    def test_config_context_and_get_config_are_the_same(self):
        """Test that get_config() within a config contextmanager is the same config."""

        _first_config = config.get_config()

        with config.temp_config() as _temp_config:
            self.assertEquivalentNestedChainMap(
                _temp_config,
                _first_config.__dict__(),
                msg="Initial temporary config is different to config from before.",
            )

            _temp_config["config_version"] += ".new"
            self.assertNotEqual(
                _temp_config["config_version"],
                _first_config["config_version"],
                msg="Modifying root entry in temp config modified the previous config from outside the contextmanager.",
            )
            self.assertEquivalentNestedChainMap(
                _temp_config,
                config.get_config().__dict__(),
                msg="get_config() and current temporary config do not match after modifying root entry.",
            )

            _temp_config["storage_providers"]["folder_storage_provider"]["temp_dir"] = (
                "/this_is_a_test"
            )
            self.assertNotEqual(
                _temp_config["storage_providers"]["folder_storage_provider"][
                    "temp_dir"
                ],
                _first_config["storage_providers"]["folder_storage_provider"][
                    "temp_dir"
                ],
                msg="Modifying nested entry in temp config modified the previous config from outside the contextmanager.",
            )
            self.assertEquivalentNestedChainMap(
                _temp_config,
                config.get_config().__dict__(),
                msg="get_config() and current temporary config do not match after modifying nested entry.",
            )

    def test_config_context_overwrite(self):
        """Test temp_config doesn't overwrite old configs, within a context manager."""
        # Get current config and save it as a dictionary for comparisons
        _first_config = config.get_config()
        _first_dict = _first_config.__dict__()  # pyright: ignore[reportCallIssue]
        # For our own sanity, verify that the __dict__ value is the same as the config.
        self.assertEquivalentNestedChainMap(
            _first_config, _first_dict, "__dict__ and first config do not match."
        )

        # Decide on the value to change
        _new_version = _first_config["config_version"] + ".new"
        _new_root_dir = join(
            _first_config["storage_providers"]["folder_storage_provider"]["root_dir"],
            "data",
        )

        # Enter context
        with config.temp_config() as _temp_config:
            self.assertEquivalentNestedChainMap(
                _temp_config,
                _first_dict,
                "temp_config() doesn't match previous context config.",
            )
            _temp_config["config_version"] = _new_version
            _temp_config["storage_providers"]["folder_storage_provider"]["root_dir"] = (
                _new_root_dir
            )

            # Assert that we didn't modify the first config
            self.assertNotEqual(
                _first_config["config_version"],
                _new_version,
                "Modifications to root key of temp_config() also modify original config.",
            )
            self.assertNotEqual(
                _first_config["storage_providers"]["folder_storage_provider"][
                    "root_dir"
                ],
                _new_root_dir,
                "Modifications to nested key of temp_config() also modify original config.",
            )

            # Assert that we did modify the current context's config
            self.assertEqual(
                _temp_config["config_version"],
                _new_version,
                "Modifications to root key of temp_config() were not applied.",
            )
            self.assertEqual(
                _temp_config["storage_providers"]["folder_storage_provider"][
                    "root_dir"
                ],
                _new_root_dir,
                "Modifications to nested key of temp_config() were not applied.",
            )
            # Assert that we modified the current config with get_config()
            self.assertEqual(
                config.get_config()["config_version"],
                _new_version,
                "Modifications to root key of temp_config() were not applied.",
            )
            self.assertEqual(
                config.get_config()["storage_providers"]["folder_storage_provider"][
                    "root_dir"
                ],
                _new_root_dir,
                "Modifications to nested key of temp_config() were not applied.",
            )

            # There's no equivalent of assertNotEquivalent, so we capture
            # assertions instead.
            with self.assertRaises(AssertionError):
                self.assertEquivalentNestedChainMap(
                    _first_config, _temp_config.__dict__()
                )

        self.assertEquivalentNestedChainMap(_first_config, _first_dict)
        self.assertNotEqual(_first_config["config_version"], _new_version)

    def test_config_nested_context_overwrite(self):
        """Test temp_config doesn't overwrite old configs, within nested context managers."""
        # Get current config and save it as a dictionary for comparisons
        _original_config = config.get_config()
        _original_dict = _original_config.__dict__()  # pyright: ignore[reportCallIssue]
        # For our own sanity, verify that the __dict__ value is the same as the config.
        self.assertEquivalentNestedChainMap(
            _original_config,
            _original_dict,
            "__dict__ of initial config doesn't match config.",
        )

        # Decide on the value to change
        _version_original = _original_config["config_version"]
        _version_first_context = _version_original + ".new"
        _version_second_context = _version_first_context + ".ultra_new"
        _root_dir_original = _original_config["storage_providers"][
            "folder_storage_provider"
        ]["root_dir"]
        _root_dir_first_context = join(
            _root_dir_original,
            "subdata",
        )

        # Enter context
        with config.temp_config() as _first_context_config:
            # Modify first context. We don't test it here as it's tested in
            # test_config_context_overwrite
            _first_context_config["config_version"] = _version_first_context
            _first_context_config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ] = _root_dir_first_context

            # Create a dictionary of the second config, for later comparison.
            _first_dict = _first_context_config.__dict__()  # pyright: ignore[reportCallIssue]

            # Enter second context and modify further.
            with config.temp_config() as _second_context_config:
                # Double check that _second_context_config is a copy of the previous config
                self.assertEquivalentNestedChainMap(
                    _second_context_config,
                    _first_dict,
                    "temp_config() doesn't match previous context config.",
                )
                # Modify the inner context's config
                _second_context_config["config_version"] = _version_second_context

                # Assert that modifications did modify the current config
                self.assertEqual(
                    _second_context_config["config_version"],
                    _version_second_context,
                    "Modifications to temp_config() are not applied.",
                )

                # Assert that we haven't modified parent context's configs
                self.assertNotEqual(
                    _original_config["config_version"],
                    _version_second_context,
                    "Modifications to temp_config() also modify original config.",
                )
                self.assertNotEqual(
                    _first_context_config["config_version"],
                    _version_second_context,
                    "Modifications to temp_config() also modify previous context's config.",
                )

                # Assert that we carry through modifications from the previous
                # context that weren't present in the original config.
                self.assertEqual(
                    _second_context_config["storage_providers"][
                        "folder_storage_provider"
                    ]["root_dir"],
                    _root_dir_first_context,
                )

                # There's no equivalent of assertNotEquivalent, so we capture
                # assertions instead.
                with self.assertRaises(
                    AssertionError,
                    msg="Modifications to second context config modified the original config.",
                ):
                    self.assertEquivalentNestedChainMap(
                        _second_context_config, _original_dict
                    )
                with self.assertRaises(
                    AssertionError,
                    msg="Modifications to second context config modified the first context's config.",
                ):
                    self.assertEquivalentNestedChainMap(
                        _second_context_config, _first_dict
                    )

            # Check __exit__ of inner context
            self.assertEquivalentNestedChainMap(_first_context_config, _first_dict)
            self.assertEqual(
                _first_context_config["config_version"],
                _version_first_context,
                "A root key of first context was modified by inner context.",
            )
            self.assertEqual(
                _first_context_config["storage_providers"]["folder_storage_provider"][
                    "root_dir"
                ],
                _root_dir_first_context,
                "A nested key of first context modified by inner context.",
            )

        # Check __exit__ from all contexts
        self.assertEqual(
            _original_config["config_version"],
            _version_original,
            "Original config version, a root key, was modified in other contexts.",
        )
        self.assertEqual(
            _original_config["storage_providers"]["folder_storage_provider"][
                "root_dir"
            ],
            _root_dir_original,
            "Original config root_dir, in a nested position, was modified in other contexts.",
        )
        self.assertEquivalentNestedChainMap(
            _original_config,
            _original_dict,
            "Original config was modified in contexts.",
        )
