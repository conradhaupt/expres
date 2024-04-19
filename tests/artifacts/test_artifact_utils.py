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

import asdf
import ddt
from aardvark.artifacts import ArtifactInfo
from aardvark.artifacts.utils import (
    artifacts_from_asdf,
    replace_values_with_artifacts,
    restore_values_for_artifacts,
)
from aardvark.asdf.tags import ArtifactInfoTag
from aardvark.utils.tests import TestCase


@ddt.ddt
class TestArtifactUtils_artifacts_from_asdf(TestCase):
    """Tests for :fun:`artifacts_from_asdf` artifact utility function."""

    def test_correct_artifacts(self):
        tree = asdf.AsdfFile()
        tree["x"] = 0
        tree["y"] = 0.0
        tree["a"] = ArtifactInfo(
            file="file.txt",
            name="a",
            format="npz",
            floating=False,
        )
        tree["b"] = ArtifactInfo(
            file="execution.log",
            name="b",
            format="npz",
            floating=False,
        )

        expected_artifacts = {tree["a"], tree["b"]}
        actual_artifacts = set(artifacts_from_asdf(tree))
        self.assertEqual(expected_artifacts, actual_artifacts)

    def test_ignores_deep_artifacts(self):
        tree = asdf.AsdfFile()
        tree["x"] = 0
        tree["y"] = 0.0
        tree["z"] = {
            0: ArtifactInfo(
                file="not_correct.npz", name="c", format="npz", floating=False
            )
        }
        tree["a"] = ArtifactInfo(
            file="file.txt",
            name="a",
            format="npz",
            floating=False,
        )
        tree["b"] = ArtifactInfo(
            file="execution.log",
            name="b",
            format="npz",
            floating=False,
        )

        expected_artifacts = {tree["a"], tree["b"]}
        actual_artifacts = set(artifacts_from_asdf(tree))
        self.assertEqual(expected_artifacts, actual_artifacts)

    def test_raises_on_incorrect_name_for_bound_artifact(self):
        tree = asdf.AsdfFile()
        tree["a"] = ArtifactInfo(file="a.npz", name="b", format="npz", floating=False)
        with self.assertRaisesRegex(
            ValueError,
            "has the wrong name",
            msg=(
                "artifacts_from_asdf should raise an error if "
                "a bound artifact name does not match the attribute name."
            ),
        ):
            _ = artifacts_from_asdf(tree)

    def test_raises_on_floating_artifact(self):
        tree = asdf.AsdfFile()
        tree["a"] = ArtifactInfo(file="a.npz", name="b", floating=True)
        with self.assertRaisesRegex(
            ValueError,
            "should not contain floating ArtifactInfo instances",
            msg=(
                "artifacts_from_asdf should raise an error if "
                "it encounters a floating artifact."
            ),
        ):
            _ = artifacts_from_asdf(tree)

    def test_correctly_handles_artifactinfotags(self):
        tree = asdf.AsdfFile()
        tree["a"] = ArtifactInfoTag(source="file.txt", floating=False, format="npz")

        expected_artifact = ArtifactInfo(
            file="file.txt", name="a", format="npz", floating=False
        )
        actual_artifact = artifacts_from_asdf(tree)[0]
        self.assertEqual(expected_artifact, actual_artifact)

    def test_correctly_handles_artifactinfotags_with_name(self):
        tree = asdf.AsdfFile()
        tree["a"] = ArtifactInfoTag(
            source="file.txt", name="a", floating=False, format="npz"
        )

        expected_artifact = ArtifactInfo(
            file="file.txt", name="a", format="npz", floating=False
        )
        actual_artifact = artifacts_from_asdf(tree)[0]
        self.assertEqual(expected_artifact, actual_artifact)

    def test_raises_for_artifactinfotag_with_incorrect_name(self):
        tree = asdf.AsdfFile()
        tree["a"] = ArtifactInfoTag(
            source="file.txt", name="incorrect", floating=False, format="npz"
        )

        expected_artifact = ArtifactInfo(
            file="file.txt", name="a", format="npz", floating=False
        )
        with self.assertRaisesRegex(
            ValueError,
            "that does not match attribute",
            msg=(
                "artifacts_from_asdf should raise if an ArtifactInfoTag has a name that"
                " isn't the attribute name."
            ),
        ):
            _ = artifacts_from_asdf(tree)


@ddt.ddt
class TestArtifactUtils_replace_values_with_artifacts(TestCase):
    """Tests for :fun:`replace_values_with_artifacts` artifact utility function."""

    def setUp(self) -> None:
        super().setUp()
        self.artifact1 = ArtifactInfo(
            file="file1.txt", name="file1", format="npz", floating=False
        )
        self.artifact2 = ArtifactInfo(
            file="file2.txt", name="file2", format="npz", floating=False
        )
        self.artifact3 = ArtifactInfo(
            file="file3.txt", name="file3", format="npz", floating=False
        )
        self.artifact4 = ArtifactInfo(
            file="file4.txt", name="file4", format="npz", floating=False
        )

    def test_correctly_replaces_values(self):
        tree = asdf.AsdfFile()
        values = {
            "file1": 0,
            "file2": 1,
            "file3": 2,
            "file4": 4,
        }
        artifacts = {
            "file1": self.artifact1,
            "file2": self.artifact2,
            "file3": self.artifact3,
            "file4": self.artifact4,
        }
        for k, v in values.items():
            tree[k] = v

        expected_tree = tree.copy()
        selected_keys = ["file1", "file3"]
        for k in values.keys():
            if k in selected_keys:
                expected_tree[k] = artifacts[k]
            else:
                expected_tree[k] = values[k]

        self.assertNotEqual(
            tree,
            expected_tree,
            msg="Trees with and without artifacts should not be equal.",
        )
        extracted_values = replace_values_with_artifacts(
            tree, artifacts=[a for k, a in artifacts.items() if k in selected_keys]
        )

        for k in tree.keys():
            self.assertEqual(
                tree[k],
                expected_tree[k],
                msg="Value for tree[{}] should be equal.".format(k),
            )
        self.assertEqual(
            extracted_values, {k: v for k, v in values.items() if k in selected_keys}
        )

    def test_raises_with_duplicate_names(self):
        tree = asdf.AsdfFile()
        values = {
            # Should be extracted.
            self.artifact4.name: -1,
            # Duplicates should cause an error
            self.artifact1.name: 0,
            "duplicate": 1,
        }
        artifacts = {
            # Should be extracted.
            self.artifact4.name: self.artifact4,
            # Duplicates should cause an error
            self.artifact1.name: self.artifact1,
            "duplicate": ArtifactInfo(
                file="file2.txt", name=self.artifact1.name, format="npz", floating=False
            ),
        }
        for k, v in values.items():
            tree[k] = v
        original_tree = tree.copy()

        with self.assertRaisesRegex(
            ValueError,
            "Cannot replace multiple artifacts with name",
            msg=(
                "replace_values_with_artifacts should raise an error if "
                "`artifacts` contains artifacts with the same name."
            ),
        ):
            _ = replace_values_with_artifacts(tree, artifacts=artifacts.values())

        # replace_values_with_artifacts should recover and not result in a
        # broken tree if it fails.
        for k in tree.keys():
            self.assertEqual(
                tree[k],
                original_tree[k],
                msg=(
                    "Value for tree[{}] should be unchanged if an error occurred.".format(
                        k
                    )
                ),
            )

    def test_raises_with_missing_attribute(self):
        tree = asdf.AsdfFile()
        values = {
            "file1": 0,
        }
        artifacts = {
            "file1": self.artifact1,
            "file2": self.artifact2,
        }
        for k, v in values.items():
            tree[k] = v

        with self.assertRaisesRegex(
            KeyError,
            "not found in ASDF tree",
            msg=(
                "replace_values_with_artifacts should raise an error if an artifact"
                " name/attr is not found in the ASDF tree."
            ),
        ):
            _ = replace_values_with_artifacts(tree, artifacts=artifacts.values())


@ddt.ddt
class TestArtifactUtils_restore_values_for_artifacts(TestCase):
    """Tests for :fun:`restore_values_for_artifacts` artifact utility function."""

    def setUp(self) -> None:
        super().setUp()
        self.artifact1 = ArtifactInfo(
            file="file1.txt", name="file1", format="npz", floating=False
        )
        self.artifact2 = ArtifactInfo(
            file="file2.txt", name="file2", format="npz", floating=False
        )
        self.artifact3 = ArtifactInfo(
            file="file3.txt", name="file3", format="npz", floating=False
        )
        self.artifact4 = ArtifactInfo(
            file="file4.txt", name="file4", format="npz", floating=False
        )

    def test_correctly_restores_values(self):
        tree = asdf.AsdfFile()
        values = {
            "file1": 0,
            "file2": 1,
            "file3": 2,
            "file4": 4,
        }
        artifacts = {
            "file1": self.artifact1,
            "file2": self.artifact2,
            "file3": self.artifact3,
            "file4": self.artifact4,
        }
        for k, v in values.items():
            tree[k] = v

        expected_tree = tree.copy()
        selected_keys = ["file1", "file3"]
        # We test replace_values_with_artifacts somewhere else, so we don't test
        # it here.
        extracted_values = replace_values_with_artifacts(
            tree, artifacts=[a for k, a in artifacts.items() if k in selected_keys]
        )

        for k in selected_keys:
            self.assertTrue(tree[k], ArtifactInfo)

        self.assertEqual(
            extracted_values, {k: v for k, v in values.items() if k in selected_keys}
        )

        restore_values_for_artifacts(
            tree,
            artifacts=[a for k, a in artifacts.items() if k in selected_keys],
            values=extracted_values,
        )

        for k in tree.keys():
            if k not in selected_keys:
                self.assertEqual(
                    tree[k],
                    expected_tree[k],
                    msg="Value for tree[{}] should be left unmodified.".format(k),
                )
            else:
                self.assertEqual(
                    tree[k],
                    expected_tree[k],
                    msg="Value for tree[{}] was not restored correctly.".format(k),
                )
