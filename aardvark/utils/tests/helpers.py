# This code is part of Aardvark.
#
# Copyright 2024-2026 Conrad Haupt <conrad@conradhaupt.com> and IBM.
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

from io import BytesIO
from typing import TYPE_CHECKING
from unittest import TestCase as UnitTestTestCase

import asdf

if TYPE_CHECKING:
    from qiskit.primitives.containers import DataBin


def roundtrip_object(obj, version=None, lazy_load: bool = False):
    """Add the specified object to an AsdfFile's tree, write the file to
    a buffer, then read it back in and return the deserialized object.

    Args:
        obj: The object to round-trip.
        version: Optional version of the ASDF file to serialise to. Defaults to
            None.
        lazy_load: Whether the ASDF file should be opened with lazy_load.
            Defaults to False.

    Returns:
        The round-trip object, having been serialised and deserialised.
    """
    buff = BytesIO()
    with asdf.AsdfFile(version=version) as af:
        af["obj"] = obj
        af.write_to(buff)

    buff.seek(0)
    with asdf.open(buff, lazy_load=lazy_load, memmap=False) as af:
        return af["obj"]
