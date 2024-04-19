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

import tempfile as Temp
from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID

import asdf
import ddt
import pytest
from aardvark.storage import FolderProvider
from aardvark.utils.tests import TestCase

from aardvark import Experiment, dataclass, field

DUMMY_UUID = UUID(hex="83cff1b092b24f548befbbdf08fd416c")
DUMMY_DATETIME = datetime.now(tz=timezone.utc)


@dataclass(kw_only=True)
class MockExperiment(Experiment):
    tree1: int
    tree2: dict[str, str]


def get_experiment() -> MockExperiment:
    _instance = MockExperiment(
        tree1=0,
        tree2={"A": "A", "B": "B"},
    )
    _instance.uuid = DUMMY_UUID
    _instance.set_date_created(DUMMY_DATETIME)
    return _instance


def get_experiment_and_root_dir() -> tuple[MockExperiment, str]:
    root_dir = Temp.mkdtemp(prefix="aardvark_tests_")
    provider = FolderProvider()
    _instance = get_experiment()
    _instance._context = provider.new_context()
    return _instance, root_dir


@ddt.ddt
class TestExperimentAttributes(TestCase):
    """Test dataclass attributes of Experiments."""

    def test_attrs(self):
        exp = get_experiment()
        # Here we access the attributes normally, which means we should get the
        # correct values.
        self.assertEqual(exp.tree1, 0)
        self.assertEqual(exp.tree2, {"A": "A", "B": "B"})

        # Test that the attributes are in the correct places
        #
        # In the tree
        #
        _tree = exp._tree
        self.assertTrue("tree1" in _tree)
        self.assertTrue("tree2" in _tree)
        # "In" the object
        #
        _hasattr = object.__getattribute__
        with self.assertRaises(AttributeError):
            _hasattr(exp, "tree1")
        with self.assertRaises(AttributeError):
            _hasattr(exp, "tree2")

    def test_other_attributes(self):
        exp = get_experiment()
        # Try setting an attribute that is neither in the tree or an artifact
        exp.other_attr = 0

        self.assertTrue("other_attr" not in exp._tree)
        self.assertTrue("other_attr" not in exp._tree_attrs)

    def test_registering_new_attribute(self):
        exp = get_experiment()
        # Register attribute and then set
        exp.register_tree_attribute("other_attr")
        exp.other_attr = 0

        self.assertTrue("other_attr" in exp._tree)
        self.assertTrue("other_attr" not in exp._class_tree_attrs())
        self.assertTrue("other_attr" in exp._tree_attrs)

    def test_registering_existing_attribute(self):
        exp = get_experiment()
        # Set attribute and then register
        exp.other_attr = 0
        exp.register_tree_attribute("other_attr")

        self.assertTrue("other_attr" in exp._tree)
        self.assertTrue("other_attr" not in exp._class_tree_attrs())
        self.assertTrue("other_attr" in exp._tree_attrs)
        _getattr = object.__getattribute__
        with self.assertRaises(AttributeError):
            _getattr(self, "other_attr")

    def test_deregistering_existing_attribute(self):
        exp = get_experiment()
        # Set attribute, register, then deregister
        exp.other_attr = 0
        exp.register_tree_attribute("other_attr")
        exp.deregister_tree_attribute("other_attr")

        self.assertTrue("other_attr" not in exp._tree)
        self.assertTrue("other_attr" not in exp._class_tree_attrs())
        self.assertTrue("other_attr" not in exp._tree_attrs)
        _getattr = object.__getattribute__
        self.assertEqual(_getattr(exp, "other_attr"), 0)

    def test_deregistering_new_attribute(self):
        exp = get_experiment()
        # Register, set attribute, then deregister
        exp.register_tree_attribute("other_attr")
        exp.other_attr = 0
        exp.deregister_tree_attribute("other_attr")

        self.assertTrue("other_attr" not in exp._tree)
        self.assertTrue("other_attr" not in exp._class_tree_attrs())
        self.assertTrue("other_attr" not in exp._tree_attrs)
        _getattr = object.__getattribute__
        self.assertEqual(_getattr(exp, "other_attr"), 0)

    def test_registering_class_attribute(self):
        exp = get_experiment()
        with self.assertWarns(Warning):
            exp.register_tree_attribute("tree1")
        self.assertTrue("tree1" in exp._class_tree_attrs())
        self.assertTrue("tree1" in exp._tree_attrs)

    def test_deregistering_class_attribute(self):
        exp = get_experiment()

        with self.assertRaises(AttributeError):
            exp.deregister_tree_attribute("tree1")

    def test_deregister_unknown_attribute(self):
        exp = get_experiment()

        with self.assertRaises(AttributeError):
            exp.deregister_tree_attribute("doesn't exist")

    def test_dataclass_fields(self):
        exp = get_experiment()
        self.assertEqual(
            set(exp.__dataclass_fields__.keys()),
            {
                "tree1",
                "tree2",
                # There will always be the following attributes
                "uuid",
                "date_created",
                "description",
            },
        )


@ddt.ddt
class TestExperimentAttributesRoundTrip(TestCase):
    """Test round-trip success of Experiment attributes."""

    def test_init_attr_normal(self):
        @dataclass
        class TestExperiment(Experiment):
            tree_required: int

        value = 0
        exp = TestExperiment(tree_required=value)
        self.assertEqual(exp.tree_required, value)

        roundtrip_exp = self.roundtrip_experiment(exp)

        try:
            self.assertEqual(
                roundtrip_exp.tree_required,
                exp.tree_required,
                msg="Tree attribute has a different value.",
            )
        except KeyError as e:
            raise pytest.fail("Tree attribute lost during roundtrip serialisation.")

    def test_init_attr_default(self):
        @dataclass
        class TestExperiment(Experiment):
            tree_required: int = field(default=0)

        value = 0
        exp = TestExperiment()
        self.assertEqual(exp.tree_required, value)

        roundtrip_exp = self.roundtrip_experiment(exp)

        try:
            self.assertEqual(
                roundtrip_exp.tree_required,
                exp.tree_required,
                msg="Tree attribute has a different value.",
            )
        except KeyError as e:
            raise pytest.fail("Tree attribute lost during roundtrip serialisation.")

    @pytest.mark.xfail(
        reason="default=... does not use __setattr__ with init=False. Must be implemented in __post_init__."
    )
    def test_init_attr_default_init_false(self):
        @dataclass
        class TestExperiment(Experiment):
            tree_required: int = field(default=0, init=False)

        value = 0
        exp = TestExperiment()
        self.assertEqual(exp.tree_required, value)

        roundtrip_exp = self.roundtrip_experiment(exp)

        try:
            self.assertEqual(
                roundtrip_exp.tree_required,
                exp.tree_required,
                msg="Tree attribute has a different value.",
            )
        except KeyError:
            raise pytest.fail("Tree attribute lost during roundtrip serialisation.")

    def test_init_attr_defaultfactory(self):
        @dataclass
        class TestExperiment(Experiment):
            tree_required: int = field(default_factory=lambda: 0)

        value = 0
        exp = TestExperiment()
        self.assertEqual(exp.tree_required, value)

        roundtrip_exp = self.roundtrip_experiment(exp)

        try:
            self.assertEqual(
                roundtrip_exp.tree_required,
                exp.tree_required,
                msg="Tree attribute has a different value.",
            )
        except KeyError as e:
            raise pytest.fail("Tree attribute lost during roundtrip serialisation.")

    def test_init_attr_defaultfactory_init_false(self):
        @dataclass
        class TestExperiment(Experiment):
            tree_required: int = field(default_factory=lambda: 0, init=False)

        value = 0
        exp = TestExperiment()
        self.assertEqual(exp.tree_required, value)

        roundtrip_exp = self.roundtrip_experiment(exp)

        try:
            self.assertEqual(
                roundtrip_exp.tree_required,
                exp.tree_required,
                msg="Tree attribute has a different value.",
            )
        except KeyError as e:
            raise pytest.fail("Tree attribute lost during roundtrip serialisation.")

    def test_new_attribute_default_on_load(self):
        @dataclass
        class FirstExperiment(Experiment):
            tree1: int

        exp = FirstExperiment(tree1=0)
        buff = BytesIO()
        exp._tree.write_to(buff)
        buff.seek(0)
        tree = asdf.open(buff)

        @dataclass
        class SecondExperiment(Experiment):
            tree1: int
            tree2: int = field(default=10)

        new_exp = SecondExperiment.__new__(SecondExperiment, tree=tree.copy())
        try:
            self.assertEqual(new_exp.tree2, 10)
        except KeyError:
            self.fail("New field, with default, not set on loaded experiment.")

    def test_new_attribute_default_on_load(self):
        @dataclass
        class FirstExperiment(Experiment):
            tree1: int

        exp = FirstExperiment(tree1=0)
        buff = BytesIO()
        exp._tree.write_to(buff)
        buff.seek(0)
        tree = asdf.open(buff)

        @dataclass
        class SecondExperiment(Experiment):
            tree1: int
            tree2: int = field(default=10)

        with self.assertWarnsRegex(
            Warning, expected_regex="does not exist in ASDF tree. Setting to default"
        ):
            new_exp = SecondExperiment.__new__(SecondExperiment, tree=tree.copy())
        try:
            self.assertEqual(new_exp.tree2, 10)
        except KeyError:
            self.fail("New field, with default, not set on loaded experiment.")

    def test_new_attribute_default_factory_on_load(self):
        @dataclass
        class FirstExperiment(Experiment):
            tree1: int

        exp = FirstExperiment(tree1=0)
        buff = BytesIO()
        exp._tree.write_to(buff)
        buff.seek(0)
        tree = asdf.open(buff)

        class DefaultFactory:
            def __init__(self, init: int):
                self.init = init

            def __call__(self) -> tuple[int]:
                _return = self.init
                self.init += 1
                return (_return,)

        @dataclass
        class SecondExperiment(Experiment):
            tree1: int
            tree2: tuple[int] = field(default_factory=DefaultFactory(init=0))

        with self.assertWarnsRegex(
            Warning,
            expected_regex="does not exist in ASDF tree. Setting to result from default_factory\\(\\):",
        ):
            new_exp = SecondExperiment.__new__(
                SecondExperiment,
                tree=tree.copy(),
            )
        try:
            self.assertEqual(new_exp.tree2, (0,))
        except KeyError:
            self.fail("New field, with default_factory, not set on loaded experiment.")

        # Test that we are actually calling default_factory instead of just caching its value.
        with self.assertWarnsRegex(
            Warning,
            expected_regex="does not exist in ASDF tree. Setting to result from default_factory\\(\\):",
        ):
            second_new_exp = SecondExperiment.__new__(
                SecondExperiment, tree=tree.copy()
            )
        try:
            self.assertEqual(second_new_exp.tree2, (1,))
        except KeyError:
            self.fail(
                "default_factory() value is not unique per call to __new__, for new field."
            )

    def test_new_attribute_without_default_on_load(self):
        @dataclass
        class FirstExperiment(Experiment):
            tree1: int

        exp = FirstExperiment(tree1=0)
        buff = BytesIO()
        exp._tree.write_to(buff)
        buff.seek(0)
        tree = asdf.open(buff)

        @dataclass
        class SecondExperiment(Experiment):
            tree1: int
            tree2: int

        with self.assertWarnsRegex(
            Warning,
            expected_regex="has no default or default_factory in {}, and isn't in ASDF tree. Leaving unassigned.".format(
                SecondExperiment.__name__
            ),
        ):
            new_exp = SecondExperiment.__new__(SecondExperiment, tree=tree.copy())
        with self.assertRaises(
            KeyError,
            msg="Unassigned new tree attribute, without default, should raise an error when accessed.",
        ):
            _ = new_exp.tree2
