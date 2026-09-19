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

import os
from collections import deque
from collections.abc import MutableMapping
from io import BytesIO
from tempfile import mkdtemp
from typing import Any, NoReturn, TypeVar
from unittest import TestCase as UnitTestTestCase

import asdf

from aardvark import Experiment
from aardvark.utils.containers import NestedChainMap

E = TypeVar("E", bound=Experiment)


class TestCase(UnitTestTestCase):
    """TestCase that provides additional asserts and functionality."""

    def setUp(self) -> None:
        super().setUp()
        self._home = mkdtemp()
        self._previous_home = os.environ["HOME"]
        os.environ["HOME"] = self._home

    def tearDown(self) -> None:
        os.environ["HOME"] = self._previous_home

    def roundtrip_experiment(self, experiment: E) -> E:
        """Return a 'copy' of ``experiment`` that has been through a round-trip serialisation.

        Note that this does not manage storage providers and contexts. Instead
        it just provides a new Experiment with the same tree.

        Args:
            experiment: Experiment instance.

        Returns:
            A new instance of the same experiment subclass that has been
            serialised and deserialised.
        """
        file_buffer = BytesIO()
        experiment._tree.write_to(file_buffer)
        file_buffer.seek(0)
        _tree = asdf.open(file_buffer)
        roundtrip_experiment = experiment.__class__.__new__(
            experiment.__class__, tree=_tree, context=experiment._context
        )
        return roundtrip_experiment

    def assertEquivalentNestedChainMap(
        self,
        nested: NestedChainMap,
        expected: dict,
        msg: str | None = None,
    ) -> None | NoReturn:
        """Assert that ``nested`` is equivalent to the expected dictionary.

        Args:
            nested: A :class:`NestedChainMap` instance.
            expected: The expected dictionary representing the interface to ``nested``.
            msg: Optional message if assertion fails. Defaults to None.
        Raises:
            AssertionError: If the assertion fails.
        """

        self.assertIsInstance(nested, NestedChainMap)
        self.assertIsInstance(expected, dict)

        if msg is None:
            msg = "NestedChainMap is not equivalent to dictionary: "
        else:
            msg = msg + ": "

        comparison_queue: deque[
            tuple[MutableMapping[Any, Any], dict[str, Any], list[str]]
        ] = deque([(nested, expected, [])])

        def path_to_keys(path: list[str], key: str | None = None) -> str:
            if len(path) == 0:
                if key is None:
                    return "root"
                else:
                    return "[{!r}]".format(key)
            else:
                _path = "".join("[{!r}]".format(_key) for _key in path)
                if key is not None:
                    _path += "[{!r}]".format(key)
                return _path

        while comparison_queue:
            _actual, _expected, _path = comparison_queue.popleft()

            self.assertEqual(
                set(_actual.keys()),
                set(_expected.keys()),
                msg
                + "Keys of mappings at {} are not equal.".format(path_to_keys(_path)),
            )
            for _key in sorted(_expected.keys()):
                _actual_value = _actual[_key]
                _expected_value = _expected[_key]
                if isinstance(_expected_value, dict) or isinstance(
                    _actual_value, MutableMapping
                ):
                    # We have mappings. First check that both are mappings.
                    self.assertIsInstance(
                        _expected_value,
                        dict,
                        msg
                        + "Encountered mapping for actual but not expected value, for key {}".format(
                            path_to_keys(_path, _key)
                        ),
                    )
                    self.assertIsInstance(
                        _actual_value,
                        MutableMapping,
                        msg
                        + "Encountered mapping for expected value but not actual value, for key {}".format(
                            path_to_keys(_path, _key)
                        ),
                    )
                    # If we haven't asserted by now, we go down one level.
                    comparison_queue.append(
                        (_actual_value, _expected_value, [*_path, _key])
                    )
                else:
                    self.assertEqual(
                        type(_actual_value),
                        type(_expected_value),
                        msg
                        + "Types for {} values are not equal.".format(
                            path_to_keys(_path, _key)
                        ),
                    )
                    self.assertEqual(
                        _actual_value,
                        _expected_value,
                        msg
                        + "Values for {} are not equal.".format(
                            path_to_keys(_path, _key)
                        ),
                    )
