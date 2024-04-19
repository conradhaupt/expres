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

from aardvark.utils.containers import NestedChainMap
from aardvark.utils.tests import TestCase


class TestNestedChainMap_CompleteSubtrees(TestCase):
    """Test NestedChainMap when child maps override complete subtrees."""

    def test_single_mapping_one_level(self):
        base = {
            "tree0": 0,
            "tree1": "1",
            "tree2": 2.0,
            "tree3": 3 + 3j,
        }

        nested = NestedChainMap(base)
        self.assertEquivalentNestedChainMap(nested, base)

    def test_single_mapping_two_levels(self):
        base = {
            "tree0": {"subtree1": 0, "subtree2": 5},
            "tree1": "1",
            "tree2": {"subtree3": "hello world!", "subtree4": {1, 2, 3, 4, 5}},
            "tree3": 3 + 3j,
        }

        nested = NestedChainMap(base)
        self.assertEquivalentNestedChainMap(nested, base)

    def test_single_mapping_three_levels(self):
        base = {
            parent_key: {
                "tree0": {"subtree1": 0, "subtree2": 5},
                "tree1": "1",
                "tree2": {"subtree3": "hello world!", "subtree4": {1, 2, 3, 4, 5}},
                "tree3": 3 + 3j,
            }
            for parent_key in ["parenttree1", "parenttree2"]
        }

        nested = NestedChainMap(base)
        self.assertEquivalentNestedChainMap(nested, base)

    def test_two_mappings_one_level(self):
        base = {
            "common": 0,
            "uncommon": "0",
        }
        override = {
            "common": 1,
            "new": "new",
        }
        expected = {
            "common": 1,
            "uncommon": "0",
            "new": "new",
        }

        nested = NestedChainMap(base, override)
        self.assertEquivalentNestedChainMap(nested, expected)

        # Double check getting the expected values
        self.assertEqual(nested["common"], 1)
        self.assertEqual(nested["uncommon"], "0")
        self.assertEqual(nested["new"], "new")

    def test_two_mappings_two_level(self):
        """Test that subtrees are returned correctly."""
        base = {
            "common": {"common1": 0, "common2": "0"},
            "uncommon": {"uncommon1": 0.0, "uncommon2": 0.0 + 0.0j},
        }
        override = {
            "common": {"common1": 1, "common2": "1"},
            "new": {"new1": "new", "new2": "new"},
        }
        expected = {
            "common": {"common1": 1, "common2": "1"},
            "uncommon": {"uncommon1": 0.0, "uncommon2": 0.0 + 0.0j},
            "new": {"new1": "new", "new2": "new"},
        }

        nested = NestedChainMap(base, override)
        self.assertEquivalentNestedChainMap(nested, expected)

        # Double check getting the expected values
        self.assertEqual(nested["common"], {"common1": 1, "common2": "1"})
        self.assertEqual(
            nested["uncommon"], {"uncommon1": 0.0, "uncommon2": 0.0 + 0.0j}
        )
        self.assertEqual(nested["new"], {"new1": "new", "new2": "new"})

        # Double check nested values
        self.assertEqual(nested["common"]["common1"], 1)
        self.assertEqual(nested["common"]["common2"], "1")
        self.assertEqual(nested["uncommon"]["uncommon1"], 0.0)
        self.assertEqual(nested["uncommon"]["uncommon2"], 0.0 + 0.0j)
        self.assertEqual(nested["new"]["new1"], "new")
        self.assertEqual(nested["new"]["new2"], "new")

    def test_two_mappings_three_level(self):
        """Test that subtrees are returned correctly."""
        base = {
            "common": {"common1": {"common1_a": "a"}, "common2": {"common2_b": "b"}},
            "uncommon": {"uncommon1": 0.0, "uncommon2": {"uncommon2_b": 0.0 + 0.0j}},
        }
        override = {
            "common": {"common1": {"common1_a": "c"}, "common2": {"common2_b": "c"}},
            "new": {"new1": "new", "new2": {"new2a": "a"}},
        }
        expected = {
            "common": {"common1": {"common1_a": "c"}, "common2": {"common2_b": "c"}},
            "uncommon": {"uncommon1": 0.0, "uncommon2": {"uncommon2_b": 0.0 + 0.0j}},
            "new": {"new1": "new", "new2": {"new2a": "a"}},
        }

        nested = NestedChainMap(base, override)

        # Double check nested values
        self.assertEquivalentNestedChainMap(
            nested["common"]["common1"], expected["common"]["common1"]
        )
        self.assertEquivalentNestedChainMap(
            nested["common"]["common2"], expected["common"]["common2"]
        )
        self.assertEqual(
            nested["uncommon"]["uncommon1"], expected["uncommon"]["uncommon1"]
        )
        self.assertEquivalentNestedChainMap(
            nested["uncommon"]["uncommon2"], expected["uncommon"]["uncommon2"]
        )
        self.assertEqual(nested["new"]["new1"], expected["new"]["new1"])
        self.assertEquivalentNestedChainMap(
            nested["new"]["new2"], expected["new"]["new2"]
        )

        # Double check doubly-nested values
        self.assertEqual(
            nested["common"]["common1"]["common1_a"],
            expected["common"]["common1"]["common1_a"],
        )
        self.assertEqual(
            nested["common"]["common2"]["common2_b"],
            expected["common"]["common2"]["common2_b"],
        )
        self.assertEqual(
            nested["uncommon"]["uncommon2"]["uncommon2_b"],
            expected["uncommon"]["uncommon2"]["uncommon2_b"],
        )
        self.assertEqual(
            nested["new"]["new2"]["new2a"], expected["new"]["new2"]["new2a"]
        )

        # Complete equivalent check
        self.assertEquivalentNestedChainMap(nested, expected)


class TestNestedChainMap_DifferentSubtrees(TestCase):
    def test_two_mappings_two_levels(self):
        base = {
            "common": {"common1": 0, "to_be_overridden": "0"},
            "uncommon": {"uncommon1": 0.0, "uncommon2": 0.0 + 0.0j},
        }
        override = {"common": {"to_be_overridden": "1"}}

        nested = NestedChainMap(base, override)

        expected = {
            "common": {
                "common1": 0,
                "to_be_overridden": override["common"][
                    "to_be_overridden"
                ],  # Should be the overridden value
            },
            "uncommon": {"uncommon1": 0.0, "uncommon2": 0.0 + 0.0j},
        }

        self.assertEquivalentNestedChainMap(nested, expected)

    def test_three_mappings_two_levels(self):
        base = {
            "common": {"common1": 0, "to_be_overridden": "0"},
            "uncommon": {"uncommon1": 0.0, "uncommon2": 0.0 + 0.0j},
        }
        override = {"common": {"to_be_overridden": "1"}}

        nested = NestedChainMap(base, override)

        expected = {
            "common": {
                "common1": 0,
                "to_be_overridden": override["common"][
                    "to_be_overridden"
                ],  # Should be the overridden value
            },
            "uncommon": {"uncommon1": 0.0, "uncommon2": 0.0 + 0.0j},
        }

        self.assertEquivalentNestedChainMap(nested, expected)

    def test_two_mappings_three_levels(self):
        base = {
            "common": {
                "common1": {"common1": 0},
                "to_be_overridden": {
                    "to_be_overridden_1": "0",
                    "to_remain": "0.0",
                },
                "to_be_overridden_2": "0.0 + 0.0j",
            },
            "uncommon": {
                "uncommon1": 0.0,
                "uncommon2": {"val1": 0.0 + 0.0j, "val2": 0.0 + 0.0j},
            },
        }
        override = {
            "common": {
                "to_be_overridden": {
                    "to_be_overridden_1": "1",
                },
                "to_be_overridden_2": "1.0 + 1.0j",
            },
            "new": {"new1": {"new2": "new"}},
        }

        nested = NestedChainMap(base, override)

        expected = {
            "common": {
                "common1": {"common1": 0},
                "to_be_overridden": {
                    "to_be_overridden_1": override["common"]["to_be_overridden"][
                        "to_be_overridden_1"
                    ],
                    "to_remain": "0.0",
                },
                "to_be_overridden_2": override["common"]["to_be_overridden_2"],
            },
            "uncommon": {
                "uncommon1": 0.0,
                "uncommon2": {"val1": 0.0 + 0.0j, "val2": 0.0 + 0.0j},
            },
            "new": {"new1": {"new2": "new"}},
        }

        self.assertEquivalentNestedChainMap(nested, expected)

    def test_three_mappings_three_levels(self):
        base = {
            "common": {
                "common1": {"common1": 0},
                "to_be_overridden": {
                    "to_be_overridden_twice": "0",
                    "to_remain": "0.0",
                },
                "to_be_overridden_1": "0.0 + 0.0j",
            },
            "uncommon": {
                "uncommon1": 0.0,
                "uncommon2": {"val1": 0.0 + 0.0j, "val2": 0.0 + 0.0j},
            },
        }
        override_1 = {
            "common": {
                "to_be_overridden": {
                    "to_be_overridden_twice": "1",
                },
                "to_be_overridden_1": "1.0 + 1.0j",
            },
            "new": {"new1": {"new2": "new"}},
        }
        override_2 = {
            "common": {
                "to_be_overridden": {
                    "to_be_overridden_twice": "2",
                }
            },
            "new2": {"new2": "new"},
        }

        nested = NestedChainMap(base, override_1, override_2)

        expected = {
            "common": {
                "common1": {"common1": 0},
                "to_be_overridden": {
                    "to_be_overridden_twice": override_2["common"]["to_be_overridden"][
                        "to_be_overridden_twice"
                    ],
                    "to_remain": "0.0",
                },
                "to_be_overridden_1": override_1["common"]["to_be_overridden_1"],
            },
            "uncommon": {
                "uncommon1": 0.0,
                "uncommon2": {"val1": 0.0 + 0.0j, "val2": 0.0 + 0.0j},
            },
            "new": {"new1": {"new2": "new"}},
            "new2": {"new2": "new"},
        }

        self.assertEquivalentNestedChainMap(nested, expected)


class TestNestedChainMap_Modifications(TestCase):
    def test_new_child_parents(self):
        base = {
            "tree1": 0,
            "tree2": {
                "subtree1": 0,
                "subtree2": {"subsubtree1": 0},
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 0,
                }
            },
        }
        override = {
            "tree1": 1,
            "tree2": {
                "subtree2": {
                    "subsubtree1": 1,
                },
            },
        }

        nested = NestedChainMap(base, override)

        new = {
            "tree2": {
                "subtree2": {
                    "subsubtree1": 2,
                },
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 2,
                },
            },
        }

        expected_before_push = {
            "tree1": 1,
            "tree2": {
                "subtree1": 0,
                "subtree2": {"subsubtree1": 1},
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 0,
                }
            },
        }

        expected_after_push = {
            "tree1": 1,
            "tree2": {
                "subtree1": 0,
                "subtree2": {"subsubtree1": 2},
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 2,
                }
            },
        }

        self.assertEquivalentNestedChainMap(nested, expected_before_push)
        nested_child = nested.new_child(new)
        self.assertEquivalentNestedChainMap(nested_child, expected_after_push)
        nested_parent = nested_child.parents
        self.assertEquivalentNestedChainMap(nested_parent, expected_before_push)
        nested_base = nested_parent.parents
        self.assertEquivalentNestedChainMap(nested_base, base)

    def test_setitem(self):
        base = {
            "tree1": 0,
            "tree2": {
                "subtree1": 0,
                "subtree2": {"subsubtree1": 0},
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 0,
                }
            },
        }

        override_1 = {
            "tree1": -1,
        }

        override_2 = {
            "tree1": 1,
            "tree2": {
                "subtree2": {
                    "subsubtree1": 1,
                },
            },
        }

        nested = NestedChainMap(base, override_1, override_2, {})

        # Modifications at first level
        expected_first_level = {
            "tree1": 3,
            "tree2": {
                "subtree1": 0,
                "subtree2": {"subsubtree1": 1},
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 0,
                }
            },
        }
        nested["tree1"] = 3

        self.assertEquivalentNestedChainMap(nested, expected_first_level)

        # Modifications at second level
        expected_second_level = {
            "tree1": 3,
            "tree2": {
                "subtree1": 3,
                "subtree2": {"subsubtree1": 1},
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 0,
                }
            },
        }
        nested["tree2"]["subtree1"] = 3

        self.assertEquivalentNestedChainMap(nested, expected_second_level)

        # Modifications at second level
        expected_third_level = {
            "tree1": 3,
            "tree2": {
                "subtree1": 3,
                "subtree2": {"subsubtree1": 3},
            },
            "tree3": {
                "subtree1": {
                    "subsubtree1": 0,
                }
            },
        }
        nested["tree2"]["subtree2"]["subsubtree1"] = 3

        self.assertEquivalentNestedChainMap(nested, expected_third_level)
