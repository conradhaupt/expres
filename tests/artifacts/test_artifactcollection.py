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

from typing import Any

import ddt
from aardvark.artifacts import ArtifactCollection, ArtifactInfo
from aardvark.artifacts.artifact_collection import ArtifactCollection
from aardvark.utils.tests import TestCase


class ArtifactCollectionTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.artifacts: ArtifactCollection = ArtifactCollection()


@ddt.ddt
class TestArtifactCollection(ArtifactCollectionTestCase):
    """Tests for ArtifactCollection functionality."""

    def test_add_and_retrieve_by_name(self):
        artifact_1 = ArtifactInfo(
            "data/a.txt",
            name="a",
            description="first",
        )
        artifact_2 = ArtifactInfo(
            "data/b.txt",
            name="b",
            description="second",
        )
        artifact_3 = ArtifactInfo(
            "data/c.txt",
            name="c",
            description=None,
        )

        self.assertEqual(self.artifacts.num_artifacts, 0)
        self.artifacts._add_artifact(artifact=(artifact_1))
        self.assertEqual(self.artifacts.num_artifacts, 1)
        self.artifacts._add_artifact(artifact=(artifact_2))
        self.assertEqual(self.artifacts.num_artifacts, 2)
        self.artifacts._add_artifact(artifact=(artifact_3))
        self.assertEqual(self.artifacts.num_artifacts, 3)

        self.assertEqual(self.artifacts.num_floating_artifacts, 3)
        self.assertEqual(self.artifacts.num_bound_artifacts, 0)

        self.assertEqual(
            set(self.artifacts.artifacts()),
            {artifact_1, artifact_2, artifact_3},
            "Collection of artifacts differs.",
        )

        self.assertEqual(
            set(self.artifacts.names()),
            {"a", "b", "c"},
            "ArtifactInfo names are different.",
        )

        # Test for equality for each artifact
        for _artifact_name, _artifact_num, _artifact in [
            ("a", 1, artifact_1),
            ("b", 2, artifact_2),
            ("c", 3, artifact_3),
        ]:
            self.assertEqual(
                self.artifacts[_artifact_name],
                _artifact,
                "ArtifactInfo {} not equal to stored value: name={!r}.".format(
                    _artifact_num, _artifact_name
                ),
            )

    def test_add_and_retrieve_by_iterator(self):
        artifact_1 = ArtifactInfo(
            "data/a.txt",
            name="a",
            description="first",
        )
        artifact_2 = ArtifactInfo(
            "data/b.txt",
            name="b",
            description="second",
        )
        artifact_3 = ArtifactInfo(
            "data/c.txt",
            name="c",
            description=None,
        )

        self.artifacts._add_artifact(artifact=(artifact_1))
        self.artifacts._add_artifact(artifact=(artifact_2))
        self.artifacts._add_artifact(artifact=(artifact_3))

        self.assertEqual(
            set(iter(self.artifacts)),
            {artifact_1, artifact_2, artifact_3},
            "Collection of artifacts differs when "
            + "using iter(artifacts_collection).",
        )

    def test_getitem_unknown_raises_keyerror(self):
        with self.assertRaises(KeyError):
            _ = self.artifacts["missing"]

    def test_conflict_on_same_name_even_if_source_differs(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/b.txt", name="x")

        self.artifacts._add_artifact(artifact=(artifact_1))
        with self.assertRaises(
            ValueError, msg="Adding artifact with the same name doesn't raise an error."
        ):
            self.artifacts._add_artifact(artifact=(artifact_2))

        self.assertEqual(
            self.artifacts.names(),
            ["x"],
            "List of names not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts(),
            [artifact_1],
            "Artifacts not as expected.",
        )

    def test_conflict_on_same_source_even_if_name_differs(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/a.txt", name="y")

        self.artifacts._add_artifact(artifact=(artifact_1))
        with self.assertRaises(
            ValueError,
            msg="Adding artifact with the same source doesn't raise an error.",
        ):
            self.artifacts._add_artifact(artifact=(artifact_2))

        self.assertEqual(
            self.artifacts.names(),
            ["x"],
            "List of names not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts(),
            [artifact_1],
            "Artifacts not as expected.",
        )

    def test_conflict_on_same_name_and_same_source(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/a.txt", name="x")

        self.artifacts._add_artifact(artifact=(artifact_1))
        with self.assertRaises(
            ValueError,
            msg="Adding artifact with same name and source doesn't raise an error.",
        ):
            self.artifacts._add_artifact(artifact=(artifact_2))

        self.assertEqual(
            self.artifacts.names(),
            ["x"],
            "List of names not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts(),
            [artifact_1],
            "Artifacts not as expected.",
        )

    def test_description_is_ignored_for_uniqueness(self):
        artifact_1 = ArtifactInfo(
            "data/a.txt",
            name="x",
            description="first",
        )
        artifact_2 = ArtifactInfo(
            "data/a.txt",
            name="x",
            description="second",
        )

        self.artifacts._add_artifact(artifact=(artifact_1))
        with self.assertRaises(
            ValueError,
            msg="Adding artifact with same name and source, "
            + "but different descriptions, should raise an error.",
        ):
            self.artifacts._add_artifact(artifact=(artifact_2))

        self.assertTrue(
            self.artifacts.exists_for(name="x"),
            msg="Cannot find artifact with name.",
        )
        self.assertTrue(
            self.artifacts.exists_for(source="data/a.txt"),
            msg="Cannot find artifact with source.",
        )

        artifact_1.description = "updated"
        self.assertTrue(
            self.artifacts.exists_for(name="x"),
            msg="Cannot find artifact with name after modifying description.",
        )
        self.assertTrue(
            self.artifacts.exists_for(source="data/a.txt"),
            msg="Cannot find artifact with source after modifying description.",
        )

    def test_exists_for_requires_at_least_one_of_source_or_name(self):
        with self.assertRaises(
            ValueError,
            msg="Checking for existence without name or source should raise an error.",
        ):
            self.artifacts.exists_for()

    def test_exists_for_by_name_or_source_or_both(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/b.bin", name="y")
        self.artifacts._add_artifact(artifact=(artifact_1))
        self.artifacts._add_artifact(artifact=(artifact_2))

        for _name in ["x", "y"]:
            self.assertTrue(
                self.artifacts.exists_for(name=_name),
                msg="Failed existence check for artifact with name {!r}.".format(_name),
            )
        self.assertFalse(
            self.artifacts.exists_for(name="z"),
            msg="Existence check for non-existent artifact should return False.",
        )

        for _source in ["data/a.txt", "data/b.bin"]:
            self.assertTrue(
                self.artifacts.exists_for(source="data/a.txt"),
                msg="Failed existence check for artifact with source {!r}.".format(
                    _source
                ),
            )
        self.assertFalse(
            self.artifacts.exists_for(source="data/missing.txt"),
            msg="Existence check for non-existent artifact by source succeeded.",
        )

        # Check artifacts that DO exist
        for _name, _source in [("x", "data/a.txt"), ("y", "data/b.bin")]:
            self.assertTrue(
                self.artifacts.exists_for(name=_name, source=_source),
                msg="Failed existence check with name {!r} and source {!r}.".format(
                    _name,
                    _source,
                ),
            )
        # Check artifacts that DO NOT exist
        for _name, _source in [("x", "data/b.bin"), ("y", "data/a.txt")]:
            self.assertFalse(
                self.artifacts.exists_for(name=_name, source=_source),
                msg="Existence check with "
                + "name {!r} and source {!r} succeeded, but should have failed.".format(
                    _name, _source
                ),
            )

    def test_get_for_by_name(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/b.txt", name="y")
        self.artifacts._add_artifact(artifact=(artifact_1))
        self.artifacts._add_artifact(artifact=(artifact_2))

        for _name, _artifact in [("x", artifact_1), ("y", artifact_2)]:
            self.assertEqual(
                self.artifacts.get_for(name=_name),
                _artifact,
                msg="Retrieved artifact with "
                + "name {!r} is not the correct artifact.".format(
                    _name,
                ),
            )

        with self.assertRaises(
            KeyError,
            msg="Retrieving non-existent artifact by name should raise an error.",
        ):
            _ = self.artifacts.get_for(name="z")

    def test_get_for_by_source(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/b.txt", name="y")
        self.artifacts._add_artifact(artifact=(artifact_1))
        self.artifacts._add_artifact(artifact=(artifact_2))

        for _source, _artifact in [
            ("data/a.txt", artifact_1),
            ("data/b.txt", artifact_2),
        ]:
            self.assertEqual(
                self.artifacts.get_for(source=_source),
                _artifact,
                msg="Retrieved artifact with "
                + "source {!r} is not the correct artifact.".format(_source),
            )

        with self.assertRaises(
            KeyError,
            msg="Retrieving non-existent artifact by source should raise an error.",
        ):
            _ = self.artifacts.get_for(source="data/missing.txt")

    def test_get_for_by_both(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/b.txt", name="y")
        self.artifacts._add_artifact(artifact=(artifact_1))
        self.artifacts._add_artifact(artifact=(artifact_2))

        for _name, _source, _artifact in [
            ("x", "data/a.txt", artifact_1),
            ("y", "data/b.txt", artifact_2),
        ]:
            self.assertEqual(
                self.artifacts.get_for(name=_name, source=_source),
                _artifact,
                msg="Retrieved artifact with "
                + "name {!r} and source {!r} is not the correct artifact.".format(
                    _name, _source
                ),
            )

        for _name, _source in [
            ("x", "data/b.txt"),  # Correct name and source, just combined incorrectly.
            ("y", "data/a.txt"),  # Correct name and source, just combined incorrectly.
            ("z", "data/missing.txt"),  # Completely non-existent name and source.
        ]:
            with self.assertRaises(
                KeyError,
                msg="Retrieving non-existent artifact, "
                + "with name {!r} and source {!r}, should raise an error.".format(
                    _name, _source
                ),
            ):
                _ = self.artifacts.get_for(name=_name, source=_source)

    def test_collection_equality_ignores_order(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/b.txt", name="y")

        left = ArtifactCollection()
        right = ArtifactCollection()

        left._add_artifact(artifact=artifact_1)
        left._add_artifact(artifact=artifact_2)

        right._add_artifact(artifact=artifact_2)
        right._add_artifact(artifact=artifact_1)

        self.assertEqual(
            left,
            right,
            msg="Equality check on equal collections is incorrect.",
        )
        self.assertEqual(
            right,
            left,
            msg="Equality check on equal collections is incorrect.",
        )

    def test_collection_equality_unrelated(self):
        """Test that equality is false on collections with unrelated artifacts."""
        artifact_left_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_left_2 = ArtifactInfo("data/b.txt", name="y")
        artifact_right_1 = ArtifactInfo("data/c.txt", name="w")
        artifact_right_2 = ArtifactInfo("data/d.txt", name="z")

        left = ArtifactCollection()
        right = ArtifactCollection()

        left._add_artifact(artifact=artifact_left_1)
        left._add_artifact(artifact=artifact_left_2)

        right._add_artifact(artifact=artifact_right_2)
        right._add_artifact(artifact=artifact_right_1)

        self.assertNotEqual(
            left,
            right,
            msg="Equality check on not-equal collections is incorrect.",
        )
        self.assertNotEqual(
            right,
            left,
            msg="Equality check on not-equal collections is incorrect.",
        )

    def test_collection_equality_after_addition(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        artifact_2 = ArtifactInfo("data/b.txt", name="y")

        left = ArtifactCollection()
        right = ArtifactCollection()

        left._add_artifact(artifact=artifact_1)
        left._add_artifact(artifact=artifact_2)

        right._add_artifact(artifact=artifact_2)
        right._add_artifact(artifact=artifact_1)

        self.assertEqual(
            left,
            right,
            msg="Equality check on equal collections is incorrect.",
        )
        self.assertEqual(
            right,
            left,
            msg="Equality check on equal collections is incorrect.",
        )

        # Addition to right should result in False for __eq__
        artifact_3 = ArtifactInfo("data/c.txt", name="z")
        right._add_artifact(artifact=artifact_3)
        self.assertNotEqual(
            left,
            right,
            msg="Equality check after addition of artifact is incorrect.",
        )
        self.assertNotEqual(
            right,
            left,
            msg="Equality check after addition of artifact is incorrect.",
        )

    def test_eq_with_non_collection_raises(self):
        artifact_1 = ArtifactInfo("data/a.txt", name="x")
        self.artifacts._add_artifact(artifact=(artifact_1))
        with self.assertRaises(
            ValueError,
            msg="Equality comparison to non-ArtifactCollection instance "
            + "should raise an error.",
        ):
            _ = self.artifacts == object()

    @ddt.idata(
        [
            ({"name": "data"},),
            ({"source": "data.npz"},),
            ({"source": "data.npz", "name": "data"},),
        ]
    )
    @ddt.unpack
    def test_remove_artifact_double_check(self, remove_kwargs: dict[str, Any]):
        """Old test for removal, to double check other tests."""

        # *** Add artifacts
        # First artifact
        file1 = "data.npz"
        name1 = "data"
        artifact1 = ArtifactInfo(
            file=file1,
            name=name1,
            description="ArtifactInfo 1",
        )
        # Second artifact
        file2 = "figure1.pdf"
        name2 = "fig1"
        artifact2 = ArtifactInfo(
            file=file2,
            name=name2,
            description="ArtifactInfo 2",
        )
        # ArtifactInfo with default name
        file3 = "figure2.pdf"
        artifact3 = ArtifactInfo(file=file3, description="ArtifactInfo 3")

        self.artifacts._add_artifact(artifact=artifact1)
        self.artifacts._add_artifact(artifact=artifact2)
        self.artifacts._add_artifact(artifact=artifact3)

        msg = "Failed with {}".format(
            ", ".join(["{}={}".format(k, v) for k, v in remove_kwargs.items()])
        )

        # *** Assert that the artifacts exist to begin with
        # ArtifactInfo 1
        self.assertTrue(
            self.artifacts.exists_for(source="data.npz"),
            msg="ArtifactInfo 1 not found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(name="data"),
            msg="ArtifactInfo 1 not found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(source="data.npz", name="data"),
            msg="ArtifactInfo 1 not found. {}".format(msg),
        )
        # ArtifactInfo 2
        self.assertTrue(
            self.artifacts.exists_for(source="figure1.pdf"),
            msg="ArtifactInfo 2 not found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(name="fig1"),
            msg="ArtifactInfo 2 not found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(source="figure1.pdf", name="fig1"),
            msg="ArtifactInfo 2 not found. {}".format(msg),
        )
        # ArtifactInfo 3
        self.assertTrue(
            self.artifacts.exists_for(source="figure2.pdf"),
            msg="ArtifactInfo 3 not found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(name="figure2.pdf"),
            msg="ArtifactInfo 3 not found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(source="figure2.pdf", name="figure2.pdf"),
            msg="ArtifactInfo 3 not found. {}".format(msg),
        )

        # Remove the first artifact
        self.artifacts._remove_artifact(**remove_kwargs)

        # *** Assert modified collection
        # Assert that artifact 1 no longer exists
        self.assertFalse(
            self.artifacts.exists_for(source="data.npz"),
            msg="ArtifactInfo 1 still found. {}".format(msg),
        )
        self.assertFalse(
            self.artifacts.exists_for(name="data"),
            msg="ArtifactInfo 1 still found. {}".format(msg),
        )
        self.assertFalse(
            self.artifacts.exists_for(source="data.npz", name="data"),
            msg="ArtifactInfo 1 still found. {}".format(msg),
        )
        # ArtifactInfo 2 should still exist
        self.assertTrue(
            self.artifacts.exists_for(source="figure1.pdf"),
            msg="ArtifactInfo 2 no longer found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(name="fig1"),
            msg="ArtifactInfo 2 no longer found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(source="figure1.pdf", name="fig1"),
            msg="ArtifactInfo 2 no longer found. {}".format(msg),
        )
        # ArtifactInfo 3 should still exist
        self.assertTrue(
            self.artifacts.exists_for(source="figure2.pdf"),
            msg="ArtifactInfo 3 no longer found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(name="figure2.pdf"),
            msg="ArtifactInfo 3 no longer found. {}".format(msg),
        )
        self.assertTrue(
            self.artifacts.exists_for(source="figure2.pdf", name="figure2.pdf"),
            msg="ArtifactInfo 3 no longer found. {}".format(msg),
        )


@ddt.ddt
class TestArtifactCollection_addArtifact(ArtifactCollectionTestCase):
    """Tests for ArtifactCollection._add_artifact.

    These tests validate that :meth:`ArtifactCollection._add_artifact` works correctly.
    """

    def test_raise_on_artifact_and_file(self):
        with self.assertRaisesRegex(
            ValueError,
            "file and an ArtifactInfo instance",
            msg="_add_artifact does not raise an error when "
            + "both artifact and file are provided.",
        ):
            self.artifacts._add_artifact(
                file="f", artifact=ArtifactInfo(file="f", name="f")
            )

    def test_raise_on_artifact_and_name(self):
        with self.assertRaisesRegex(
            ValueError,
            "name and an ArtifactInfo instance",
            msg="_add_artifact does not raise an error when "
            + "both artifact and name are provided.",
        ):
            self.artifacts._add_artifact(
                name="f", artifact=ArtifactInfo(file="f", name="f")
            )

    def test_raise_on_artifact_and_description(self):
        with self.assertRaisesRegex(
            ValueError,
            "description and an ArtifactInfo instance",
            msg="_add_artifact does not raise an error when "
            + "both artifact and description are provided.",
        ):
            self.artifacts._add_artifact(
                description="f", artifact=ArtifactInfo(file="f", name="f")
            )

    def test_raise_on_artifact_and_format(self):
        with self.assertRaisesRegex(
            ValueError,
            "format and an ArtifactInfo instance",
            msg="_add_artifact does not raise an error when "
            + "both artifact and format are provided.",
        ):
            self.artifacts._add_artifact(
                format="npz", artifact=ArtifactInfo(file="f", name="f")
            )

    def test_raise_on_no_file(self):
        with self.assertRaisesRegex(
            ValueError,
            "file or artifact must be passed",
            msg="_add_artifact does not raise an error no parameters.",
        ):
            self.artifacts._add_artifact()
        with self.assertRaisesRegex(
            ValueError,
            "file or artifact must be passed",
            msg="_add_artifact does not raise an error when "
            + "file is not provided, only name.",
        ):
            self.artifacts._add_artifact(name="f")

    def test_raise_on_floating_with_format(self):
        with self.assertRaisesRegex(
            ValueError,
            "floating artifact with a format",
            msg="_add_artifact does not raise an error when "
            + "format is provided for a floating artifact.",
        ):
            self.artifacts._add_artifact(
                file="f",
                format="npz",
                floating=True,
            )

    def test_raise_on_bound_without_format(self):
        with self.assertRaisesRegex(
            ValueError,
            "without format",
            msg="_add_artifact does not raise an error when "
            + "creating a bound artifact with format.",
        ):
            self.artifacts._add_artifact(
                file="f",
                name="f",
                format=None,
                floating=False,
            )

    def test_raise_on_bound_without_name(self):
        with self.assertRaisesRegex(
            ValueError,
            "without a name",
            msg="_add_artifact does not raise an error when "
            + "creating a bound artifact with name.",
        ):
            self.artifacts._add_artifact(
                file="f",
                name=None,
                format="npz",
                floating=False,
            )

    def test_creates_and_adds_floating_artifact(self):
        self.artifacts._add_artifact(
            file="a_file.txt",
            name="a_name",
            description="A description",
            floating=True,
        )
        self.assertEqual(
            len(self.artifacts.artifacts()),
            1,
            msg="Expected exactly one artifact.",
        )
        self.assertEqual(
            self.artifacts.artifacts()[0].source,
            "a_file.txt",
            msg="Artifact source is not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts()[0].name,
            "a_name",
            msg="Artifact name is not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts()[0].description,
            "A description",
            msg="Artifact description is not as expected.",
        )
        self.assertIsNone(
            self.artifacts.artifacts()[0].format,
            msg="Artifact format for floating artifact should be None.",
        )
        self.assertTrue(
            self.artifacts.artifacts()[0].is_floating(),
            msg="Artifact should be floating.",
        )

    def test_creates_and_adds_bound_artifact(self):
        self.artifacts._add_artifact(
            file="a_file.txt",
            name="a_name",
            description="A description",
            format="npz",
            floating=False,
        )
        self.assertEqual(
            len(self.artifacts.artifacts()),
            1,
            msg="Expected exactly one artifact.",
        )
        self.assertEqual(
            self.artifacts.artifacts()[0].source,
            "a_file.txt",
            msg="Artifact source is not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts()[0].name,
            "a_name",
            msg="Artifact name is not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts()[0].description,
            "A description",
            msg="Artifact description is not as expected.",
        )
        self.assertEqual(
            self.artifacts.artifacts()[0].format,
            "npz",
            msg="Artifact format for bound artifact is not as expected.",
        )
        self.assertTrue(
            self.artifacts.artifacts()[0].is_bound(),
            msg="Artifact should be bound.",
        )


@ddt.ddt
class TestArtifactCollection_removeArtifact(ArtifactCollectionTestCase):
    """Tests for ArtifactCollection._remove_artifact.

    These tests validate that :meth:`ArtifactCollection._remove_artifact` works
    correctly.
    """

    def setUp(self):
        super().setUp()
        self.artifacts._add_artifact(
            file="file1.txt",
            name="file1",
        )
        self.artifacts._add_artifact(
            file="file2.txt",
            name="file2",
        )
        self.artifacts._add_artifact(
            file="file3.txt",
            name="file3",
            format="npz",
            floating=False,
        )
        self.artifacts._add_artifact(
            file="file4.txt",
            name="file4",
            format="npz",
            floating=False,
        )

        self.artifact1 = ArtifactInfo(file="file1.txt", name="file1")
        self.artifact2 = ArtifactInfo(file="file2.txt", name="file2")
        self.artifact3 = ArtifactInfo(
            file="file3.txt", name="file3", format="npz", floating=False
        )
        self.artifact4 = ArtifactInfo(
            file="file4.txt", name="file4", format="npz", floating=False
        )

    def test_raises_for_both_name_and_artifact(self):
        with self.assertRaisesRegex(
            ValueError,
            "name and artifact cannot be provided",
            msg="_remove_artifact should raise when "
            + "both name and artifact are provided.",
        ):
            self.artifacts._remove_artifact(name="file1", artifact=self.artifact1)

    def test_raises_for_both_source_and_artifact(self):
        with self.assertRaisesRegex(
            ValueError,
            "source and artifact cannot be provided",
            msg="_remove_artifact should raise when "
            + "both source and artifact are provided.",
        ):
            self.artifacts._remove_artifact(source="file1.txt", artifact=self.artifact1)

    def test_raises_for_name_not_found(self):
        with self.assertRaisesRegex(
            KeyError,
            "No artifact found for name",
            msg="_remove_artifact should raise when " + "the name is not found.",
        ):
            self.artifacts._remove_artifact(
                name="nonexistent",
            )

    def test_raises_for_source_not_found(self):
        with self.assertRaisesRegex(
            KeyError,
            "No artifact found for source",
            msg="_remove_artifact should raise when " + "the source is not found.",
        ):
            self.artifacts._remove_artifact(
                source="nonexistent",
            )

    def test_raises_for_artifact_name_not_found(self):
        with self.assertRaisesRegex(
            KeyError,
            "No artifact found for name",
            msg="_remove_artifact should raise when "
            + "the artifacts name is not found.",
        ):
            self.artifacts._remove_artifact(
                artifact=ArtifactInfo(
                    file=self.artifact1.source,
                    name="nonexistent",
                )
            )

    def test_raises_for_artifact_source_not_found(self):
        with self.assertRaisesRegex(
            KeyError,
            "No artifact found for source",
            msg="_remove_artifact should raise when "
            + "the artifacts source is not found.",
        ):
            self.artifacts._remove_artifact(
                artifact=ArtifactInfo(
                    file="nonexistent",
                    name=self.artifact1.name,
                )
            )
