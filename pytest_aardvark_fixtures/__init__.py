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

__version__ = "0.1.0"
version = __version__


import argparse
import re
import sys
import warnings
from dataclasses import dataclass
from hashlib import sha1
from os import PathLike
from os.path import dirname
from os.path import exists as path_exists
from os.path import join as path_join
from pathlib import Path
from typing import Any, Callable, ParamSpec, TypeVar
from typing import Literal as L

import asdf
import numpy as np
import pytest
from typing_extensions import Self

P = ParamSpec("P")
R = TypeVar("R")


def assert_tree_match(old_tree: asdf.AsdfFile, new_tree: asdf.AsdfFile):
    """Assert that two ASDF trees match, ignoring their ASDF library details and history.

    Args:
        old_tree: The original ASDF tree.
        new_tree: The new ASDF tree.
    """

    seen = set()
    ignore_keys = {"asdf_library", "history"}

    # Traverse trees, comparing values in subtrees.
    # Function based on assert_tree_match from ASDF.
    def recurse(old, new):
        if id(old) in seen or id(new) in seen:
            return

        seen.add(id(old))
        seen.add(id(new))

        if isinstance(old, dict) and isinstance(new, dict):
            # If we are in a mapping, apply recursively to all values.
            assert {x for x in old if x not in ignore_keys} == {
                x for x in new if x not in ignore_keys
            }
            for key in old:
                if key not in ignore_keys:
                    recurse(old[key], new[key])
        elif isinstance(old, (list, tuple)) and isinstance(new, (list, tuple)):
            # Apply recursively for list-like containers.
            assert len(old) == len(new)
            for a, b in zip(old, new):
                recurse(a, b)
        elif all(
            isinstance(obj, (np.ndarray, asdf.tags.core.NDArrayType))
            for obj in (old, new)
        ):
            # If both _trees_ are numpy arrays, compare specific attributes.
            with warnings.catch_warnings():
                # The oldest deps job tests against versions of numpy where this
                # testing function raised a FutureWarning but still functioned
                # as expected
                warnings.filterwarnings("ignore", category=FutureWarning)
                if old.dtype.fields:
                    if not new.dtype.fields:
                        msg = "arrays not equal"
                        raise AssertionError(msg)
                    for f in old.dtype.fields:
                        np.testing.assert_array_equal(old[f], new[f])
                else:
                    np.testing.assert_array_equal(old.__array__(), new.__array__())
        else:
            # Fallback for unknown types
            assert old == new, f"old={old}, new={new}"

    recurse(old_tree, new_tree)


class FolderContext:
    _current_path: Path

    def __init__(
        self,
        current_path: Path | None = None,
        state: "ContextState | None" = None,
        artifacts: "ArtifactCollection | None" = None,
    ): ...

    @classmethod
    def load(cls, file: str | PathLike[str]) -> tuple[asdf.AsdfFile, Self]: ...
    def save(
        self,
        experiment: "Experiment | asdf.AsdfFile",
        overwrite: bool = False,
        folder: str | None = None,
        asdf_write_to_kwargs: dict[str, Any] = {},
    ): ...


@dataclass(kw_only=True)
class Experiment:
    _context: FolderContext

    @classmethod
    def load(cls, file: str | PathLike[str], call_validate: bool = True) -> Self: ...

    def save(self, overwrite: bool = True): ...


def save_fixture(
    func: Callable[P, R] | None = None,
) -> Callable[P, R]:
    """Decorator to mark a fixture to be saved as an ASDF file."""

    def _mark(f: Callable[..., Any]) -> Callable[..., Any]:
        setattr(f, "__save_fixture__", True)
        return f

    return _mark(func) if func is not None else _mark


def fixture_path(fixtures_dir: str, nodeid: str, _name: str) -> str:
    """Returns a path for the given fixture and test.

    Filenames take on the form ``<nodeid>_<hash>`` where ``nodeid`` is modified
    to remove path-unsafe characters like whitespace and fullstops. ``hash`` is
    the first 16 characters of the sha1 hash of ``nodeid``, using
    :fun:`hashlib.sha1`. This is to make sure there are no collisions.

    Args:
        fixtures_dir: The root directory for saved fixtures.
        nodeid: The node id for the test.
        _name: The name of the fixture.

    Returns:
        The path to the ASDF file where this fixture will be saved/loaded.
    """
    return path_join(
        fixtures_dir,
        "{}_{}.asdf".format(
            re.sub("[^\\w\\.-]+", "_", nodeid),
            sha1(nodeid.encode("utf-8")).hexdigest()[:16],
        ),
    )


def aardvark_save_fixture(_path: str, _value: Experiment, overwrite: bool = True):
    """Save a fixture to ``_path``, with ASDF.

    All arrays are stored internally for easier file management."""
    if not overwrite and path_exists(_path):
        raise RuntimeError(
            "Cannot save fixture to file as it already exists and overwrite=False.\nPath is {}.".format(
                _path
            )
        )
    # If the path doesn't exist, create it.
    if not path_exists(dirname(_path)):
        Path(dirname(_path)).mkdir(parents=True, exist_ok=True)

    from aardvark.config import temp_config

    with temp_config() as _config:
        _config["storage_providers"]["folder_storage_provider"]["folder_format"] = (
            "experiment"
        )
        _config["storage_providers"]["folder_storage_provider"]["filename_format"] = (
            "experiment.asdf"
        )

        _context = _value._context
        _context.save(
            _value,
            folder=_path,
            asdf_write_to_kwargs={"all_array_storage": "internal"},
            overwrite=overwrite,
        )


def aardvark_load_fixture(_path: str) -> Any:
    """Load a fixture from ``_path``, with ASDF."""
    # Import Experiment from aardvark to override type-hint declaration in
    # preamble.
    from aardvark import Experiment

    return Experiment.load(Path(_path) / "experiment/experiment.asdf")


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup(
        "ASDF Fixtures", "Save/Replay fixture objects to/from pickle files"
    )
    group.addoption(
        "--aardvark-fixtures-save",
        action="store_true",
        default=False,
        help="Save annotated fixtures to ASDF files and do not run tests.",
    )
    group.addoption(
        "--aardvark-fixtures-load",
        action="store_true",
        default=False,
        help="Load fixtures from dir and pass to `saved` fixture.",
    )
    group.addoption(
        "--aardvark-fixtures-dir",
        action="append",
        dest="fixtures_dir",
        # metavar="DIR",
        default=[],
        help="Directory for saved fixtures. If saving, only one directory is allowed. Can be passed multiple times if loading, in which case tests will be run once per directory.",
    )
    group.addoption(
        "--_aardvark-multirun-child",
        action="store_true",
        default=False,
    )
    group.addoption(
        "--_aardvark-fixtures-singlerun-dir",
        dest="fixtures_dir",
        # metavar="DIR",
        default=None,
        help=argparse.SUPPRESS,
    )

    group.addoption(
        "--aardvark-fixtures-when-missing",
        dest="fixtures_missing",
        choices=("error", "skip", "none"),
        default="error",
        help="Behavior when a saved fixture is missing in load mode: "
        "'error' (raise), 'skip' (skip test), 'none' (return None). Default: error.",
    )
    group.addoption(
        "--aardvark-fixtures-overwrite",
        action="store_true",
        default=True,
        dest="fixtures_overwrite",
        help="When saving, overwrite files if they already exist (default: True).",
    )


def _replace_args_for_child_run(orig_args):
    """Replace cli arguments for child run."""
    cleaned = []
    skip_next = False
    for _arg in orig_args:
        if skip_next:
            skip_next = False
            continue
        # *** Remove fixtures dir so we can pass one directory at a time
        if _arg.startswith("--aardvark-fixtures-dir="):
            continue
        if _arg == "--aardvark-fixtures-dir":
            skip_next = True
            continue
        cleaned.append(_arg)
    return cleaned


def pytest_cmdline_main(config: pytest.Config):
    """Handle running multiple child runs, or sub-sessions; once per --aardvark-fixtures-dir.

    This is done by parsing --aardvark-fixtures-dir and invoking pytest with each
    directory. The value of this directory is stored in the hidden option
    _aardvark_fixtures_singlerun_dir.
    """
    # If we are neither loading or saving, then this plugin does nothing.
    if not config.getoption("aardvark_fixtures_load") and not config.getoption(
        "aardvark_fixtures_save"
    ):
        return None

    # We are running pytest-aardvark-fixtures, so we must modify the cli args to
    # handle multiple --aardvark-fixtures-dir values.
    is_child = config.getoption("_aardvark_multirun_child")
    dirs = config.getoption("fixtures_dir") or []
    if not isinstance(dirs, list):
        dirs = [dirs]
    save = config.getoption("--aardvark-fixtures-save")
    if save and len(dirs) > 1:
        raise pytest.UsageError(
            "Cannot save with multiple fixture directories. Got directories: \n{}".format(
                "\n".join(["\t{}".format(_dir) for _dir in dirs])
            )
        )

    # *** Split into children runs if we are the root run and we have more than one directory.
    if not is_child:
        try:
            base_args = list(config.invocation_params.args)
        except Exception:
            base_args = sys.argv[1:]

        # Remove duplicate --aardvark-fixtures-dir
        base_args = _replace_args_for_child_run(base_args)

        overall_exitcode = 0
        for _sub_dir in dirs:
            _msg = f" Running sub-session for saved directory: '{_sub_dir}'"
            _heading = _centred_heading("ASDF Fixtures", len(_msg), "=")
            print("\n{heading}\n{msg}\n{heading}\n".format(heading=_heading, msg=_msg))

            # Set hidden arguments
            child_args = base_args + [
                f"--_aardvark-fixtures-singlerun-dir={_sub_dir}",
                "--_aardvark-multirun-child",
            ]

            # Run child-run
            sub_exit = pytest.main(child_args)
            # Get the 'worst' exitcode
            overall_exitcode = max(overall_exitcode, int(sub_exit))

        return overall_exitcode

    # Run as usual, we are a child-run.
    return None


def is_saved_fixture(fixture: pytest.FixtureDef[Any]) -> bool:
    """Return if the given fixture was annotated with :fun:`save_fixture`."""
    if hasattr(fixture, "func"):
        return getattr(fixture.func, "__save_fixture__", False)
    else:
        return False


def pytest_configure(config: pytest.Config):
    """Configure pytest with options for this plugin."""
    save = config.getoption("--aardvark-fixtures-save")
    load = config.getoption("--aardvark-fixtures-load")
    if save and load:
        raise pytest.UsageError("Can either save or load fixtures, not both.")
    if not save and not load:
        # We're doing neither, so don't add our config
        return
    fixtures_dir = config.getoption("fixtures_dir")

    # NEW: capture the original CLI args for debugging/visibility
    try:
        invocation_args = list(config.invocation_params.args)
    except Exception:
        invocation_args = sys.argv[1:]

    config._aardvarkfixtures_state = {
        "save": save,
        "load": load,
        "fixtures_dir": fixtures_dir,
        "missing": config.getoption("fixtures_missing"),
        "overwrite": config.getoption("fixtures_overwrite"),
        "num_saved": 0,
        "num_loaded": 0,
        "num_missing": 0,
        "cli_args": invocation_args,
    }


def pytest_unconfigure(config: pytest.Config):
    """Remove any added config details for this plugin."""
    if hasattr(config, "_aardvarkfixtures_state"):
        delattr(config, "_aardvarkfixtures_state")


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """Handle fixtures for test functions in save mode.

    Load mode is handled by the :fun:`saved_fixtures` fixture."""

    config = pyfuncitem.session.config

    # Get plugin state and return None if it isn't configured.
    _plugin_state = getattr(config, "_aardvarkfixtures_state", {})
    if not _running_aardvark_fixtures(_plugin_state):
        return None
    if not _plugin_state.get("save", False):
        return None

    # If there aren't fixtures for this test, then we don't need to save anything
    funcargs: dict[str, Any] = getattr(pyfuncitem, "funcargs", {})
    if not funcargs:
        return True

    # *** Save fixtures
    fixtures_dir: str = _plugin_state["fixtures_dir"]
    overwrite: bool = _plugin_state["overwrite"]

    # Get fixture definitions and names
    name2defs: dict[str, list[pytest.FixtureDef[Any]]]
    name2defs = getattr(pyfuncitem, "_fixtureinfo").name2fixturedefs

    # *** Loop over fixtures and save them when necessary
    for _name, _value in funcargs.items():
        defs = name2defs.get(_name, [])
        if len(defs) == 0:
            continue

        fixturedef = defs[0]
        if not is_saved_fixture(fixturedef):
            continue

        _nodeid = pyfuncitem.nodeid
        _path = fixture_path(fixtures_dir, _nodeid, _name)
        try:
            aardvark_save_fixture(_path, _value, overwrite=overwrite)
        except Exception as e:
            raise RuntimeError(
                "[aardvark_fixture] Failed to save fixture to asdf file, with exception.",
                e,
            )
        _plugin_state["num_saved"] += 1

    # Do not execute the test function body in SAVE mode
    return True


@pytest.fixture
def saved_fixtures(request: pytest.FixtureRequest) -> dict[str, Any]:
    """Fixture containing fixtures loaded from files.

    ``request`` contains information about the function/test to which this
    fixture is being passed.
    """
    _plugin_state = getattr(request.config, "_aardvarkfixtures_state", {})
    if not isinstance(_plugin_state, dict) or len(_plugin_state) == 0:
        raise RuntimeError(
            "Expres Fixture plugin config not populated. Got {} instead of expected dictionary.".format(
                str(_plugin_state)
            )
        )

    _fixtures_dir = _plugin_state["fixtures_dir"]
    _missing: L["skip", "error", "none"] = _plugin_state["missing"]

    # If we have specified save or we haven't specified loading, return a dummy
    # dictionary.
    if _plugin_state["save"] or not _plugin_state["load"]:
        return {}

    #  *** Identify fixtures for this test.
    name2defs: dict[str, list[pytest.FixtureDef[Any]]] = {}  # pyright: ignore[reportMissingTypeArgument]
    try:
        # Hopefully this works, which means we can get the fixture definitions directly.
        name2defs = request._pyfuncitem._fixtureinfo.name2fixturedefs  # pyright: ignore[reportPrivateUsage, reportAssignmentType]
    except Exception:
        # The fixture information isn't present, so we must find it another way
        try:
            _manager = request._fixturemanager  # type: ignore[attr-defined]
        except Exception:
            _manager = None
        # If we got a fixture manager, then add all available definitions to name2defs
        if _manager is not None:
            for _fixture_name in request.fixturenames:
                _fixture_defs = _manager.getfixturedefs(_fixture_name, request.node)
                if _fixture_defs is not None:
                    name2defs[_fixture_name] = list(_fixture_defs)

    # *** Record fixtures that are not ``saved_fixtures``.
    _saved_fixtures: list[str] = [
        _name
        for _name, _defs in name2defs.items()
        if _name != "saved_fixtures"
        and _defs is not None
        and is_saved_fixture(_defs[0])
    ]

    # *** Load all fixtures that should have been saved.
    _fixture_values: dict[str, Any] = {}
    for _name in _saved_fixtures:
        _path = fixture_path(_fixtures_dir, request.node.nodeid, _name)
        # Handle non-existent saved fixtures
        if not path_exists(_path):
            if _missing == "skip":
                pytest.skip(
                    "[aardvark_fixture] Missing asdf file for fixture {} at '{}'.".format(
                        _name, _path
                    )
                )
            elif _missing == "none":
                request.config._aardvarkfixtures_state["num_missing"] += 1
                _fixture_values[_name] = None
                continue
            elif _missing == "error":
                request.config._aardvarkfixtures_state["num_missing"] += 1
                raise RuntimeError(
                    "[aardvark_fixture] Missing asdf file for fixture {} at '{}'.".format(
                        _name, _path
                    )
                )
            else:
                raise NotImplementedError(
                    "[aardvark_fixture] Encountered missing saved fixture but have unexpected missing config value '{}'.".format(
                        _missing
                    )
                )

        # Load saved values
        _fixture_values[_name] = aardvark_load_fixture(_path)
        request.config._aardvarkfixtures_state["num_loaded"] += 1
    return _fixture_values


def _centred_heading(heading: str, width: int, marker: str) -> str:
    """Centre text by padding marker on either side, up to ``width``.

    ``heading`` is centred inside the returned string, with a space to the left
    and right followed by as many markers as are necessary to return a string of
    length ``width``.

    Args:
        heading (str): The heading to centre in the heading.
        width (int): The width of the final string.
        marker (str): The marker to pad left and right of heading.

    Returns:
        The final heading centred in a line of width ``width``, padded by ``marker``.
    """
    if len(heading) >= width - 2:
        return heading
    _num_left = (width - len(heading) - 2) // 2 // len(marker)
    _num_right = (width - 2 - len(heading) - (len(marker) * _num_left)) // len(marker)
    return marker * _num_left + " {} ".format(heading) + marker * _num_right


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter, exitstatus):
    config = terminalreporter.config
    _plugin_state = getattr(config, "_aardvarkfixtures_state", None)
    if not _running_aardvark_fixtures(_plugin_state):
        return None

    # We didn't run with pytest-aardvark-fixtures, or else we would have a plugin state.
    if not isinstance(_plugin_state, dict):
        return

    # Get statistics on the number of saved, loaded, and missing fixtures.
    _num_saved = _plugin_state.get("num_saved", 0)
    _num_loaded = _plugin_state.get("num_loaded", 0)
    _num_missing = _plugin_state.get("num_missing", 0)

    # If we're saving, just report the number of saved fixtures.
    if _plugin_state["save"]:
        terminalreporter.write_line(
            "[aardvark-fixtures] Saved {} ASDF fixture files.".format(_num_saved),
            purple=True,
        )
    # If we're loading, report more detailed statistics
    if _plugin_state["load"]:
        _width = terminalreporter._screen_width
        terminalreporter.write(
            _centred_heading("Loading stats", _width, "="), purple=True
        )
        terminalreporter.write_line("Saved:   {:> 4}".format(_num_saved), purple=True)
        terminalreporter.write_line("Loaded:  {:> 4}".format(_num_loaded), purple=True)
        terminalreporter.write_line("Missing: {:> 4}".format(_num_missing), purple=True)
        terminalreporter.write_line("=" * _width, purple=True)


def pytest_report_header(config: pytest.Config):
    _plugin_state = getattr(config, "_aardvarkfixtures_state", None)

    # We didn't run with pytest-aardvark-fixtures, or else we would have a plugin state.
    if not isinstance(_plugin_state, dict):
        return None

    if not _running_aardvark_fixtures(_plugin_state):
        return None

    _saved_dir = _plugin_state.get("fixtures_dir")
    cli_args = _plugin_state.get("cli_args")
    head = []
    if _saved_dir:
        head.append(f"[aardvark_fixture] active fixtures_dir: {_saved_dir}")
    if cli_args:
        head.append(f"[aardvark_fixture] original cli rgs: {' '.join(cli_args)}")
    return "\n".join(head) if head else None


def _running_aardvark_fixtures(plugin_state: dict[str, Any]) -> bool:
    return plugin_state is not None and (
        plugin_state.get("load", False) or plugin_state.get("save", False)
    )
