# This code is part of ASDF Qiskit.
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


from asdf_qiskit.tests import TestCase
from asdf_qiskit.tests.utils import roundtrip_object
from uuid import UUID, uuid1, uuid3, uuid4, uuid5


def example_uuid(uuid_type: str) -> UUID:
    if uuid_type == "uuid1":
        return uuid1(234)
    elif uuid_type == "uuid3":
        return uuid3(namespace=UUID("31415926535897631415926535897644"), name="test")
    elif uuid_type == "uuid4":
        return uuid4()
    elif uuid_type == "uuid5":
        return uuid5(namespace=UUID("31415926535897631415926535897644"), name="test")
    elif uuid_type == "UUID":
        return UUID("31415926535897631415926535897644")
    raise NotImplementedError(
        "example_uuid not implemented for uuid type {!r}".format(uuid_type)
    )


class TestUUIDConverter(TestCase):
    """Test the UUID converter works correctly on all versions supported by the standard library."""

    def test_roundtrip_uuid(self):
        for uuid_type in ["UUID", "uuid1", "uuid3", "uuid4", "uuid5"]:
            with self.subTest(uuid_type=uuid_type):
                _uuid = example_uuid(uuid_type)
                _rt_uuid = roundtrip_object(_uuid)
                self.assertEqual(_uuid, _rt_uuid)

    def test_roundtrip_in_list(self):
        """Test roundtrip with UUID as list element."""
        for uuid_type in ["UUID", "uuid1", "uuid3", "uuid4", "uuid5"]:
            with self.subTest(uuid_type=uuid_type):
                _container = [example_uuid(uuid_type)]
                _rt_uuid = roundtrip_object(_container)
                self.assertEqual(_container, _rt_uuid)

    def test_roundtrip_in_dict(self):
        """Test roundtrip with UUID as dictionary value."""
        for uuid_type in ["UUID", "uuid1", "uuid3", "uuid4", "uuid5"]:
            with self.subTest(uuid_type=uuid_type):
                _container = {"uuid": example_uuid(uuid_type)}
                _rt_uuid = roundtrip_object(_container)
                self.assertEqual(_container, _rt_uuid)
