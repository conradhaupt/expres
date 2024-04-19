#!/usr/bin/env python3
# This code was part of Qiskit.
#
# (C) Copyright IBM 2020-2025, Conrad Haupt 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=too-many-return-statements

"""Utility script to verify aardvark copyright file headers"""

import argparse
import multiprocessing
import os
import pathlib
import sys
import re

# regex for character encoding from PEP 263
pep263 = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")
line_start = re.compile(r"^(\/\/|#) This code is part of Aardvark\.$")
copyright_line = re.compile(
    r"^(\/\/|#) Copyright [\d-]+ Conrad Haupt <conrad@conradhaupt.com> and IBM\.$"
)

IGNORE_DIRS = [
    # CMake generates some files inside the tree.
    "test/c/build",
]
IGNORE_REGEX = [
    re.compile(pattern)
    for pattern in [
        # We don't want to look at .nox environments
        r"\.tox\/",
        # We also want to ignore virtual environments
        r"\.venv\/",
    ]
]


def discover_files(code_paths):
    """Find all .py, .rs, .c, and .h files in a list of trees"""
    return [
        file
        for extension in ("py", "rs", "c", "h")
        for path in code_paths
        for file in pathlib.Path(path).glob(f"**/*.{extension}")
        # Ignore files inside IGNORE_DIRS
        if all(not file.is_relative_to(_path) for _path in IGNORE_DIRS)
        # And ignore files that match patterns
        and all(
            _regex.search(file.absolute().as_uri()) is None for _regex in IGNORE_REGEX
        )
    ]


def validate_header(file_path):
    """Validate the header for a single file"""
    header = """# This code is part of Aardvark.
#
"""
    apache_text = """#
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
"""
    header_slashes = """// This code is part of Aardvark.
//
"""
    apache_text_slashes = """//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
"""

    count = 0
    with open(file_path, encoding="utf8") as fd:
        lines = fd.readlines()
    start = 0
    for index, line in enumerate(lines):
        count += 1
        if count > 5:
            return file_path, False, "Header not found in first 5 lines"
        if count <= 2 and pep263.match(line):
            return (
                file_path,
                False,
                "Unnecessary encoding specification (PEP 263, 3120)",
            )
        if line_start.search(line):
            start = index
            break

    if file_path.suffix in (".rs", ".c", ".h"):
        if "".join(lines[start : start + 2]) != header_slashes:
            return (
                file_path,
                False,
                f"Header up to copyright line does not match: {header}",
            )
        if not copyright_line.search(lines[start + 2]):
            return (file_path, False, "Header copyright line not found")
        if "".join(lines[start + 3 : start + 15]) != apache_text_slashes:
            return (
                file_path,
                False,
                f"Header apache text string doesn't match:\n {apache_text_slashes}",
            )
    else:  # .py ending
        if "".join(lines[start : start + 2]) != header:
            return (
                file_path,
                False,
                f"Header up to copyright line does not match: {header}",
            )
        if not copyright_line.search(lines[start + 2]):
            return (file_path, False, "Header copyright line not found")
        if "".join(lines[start + 3 : start + 15]) != apache_text:
            return (
                file_path,
                False,
                f"Header apache text string doesn't match:\n {apache_text}",
            )
    return (file_path, True, None)


def _main():
    default_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "."
    )
    parser = argparse.ArgumentParser(description="Check file headers.")
    parser.add_argument(
        "paths",
        type=str,
        nargs="*",
        default=[default_path],
        help="Paths to scan by default uses `.`.",
    )
    args = parser.parse_args()
    files = discover_files(args.paths)
    with multiprocessing.Pool() as pool:
        res = pool.map(validate_header, files)
    failed_files = [x for x in res if x[1] is False]
    if len(failed_files) > 0:
        for failed_file in failed_files:
            sys.stderr.write(f"{failed_file[0]} failed header check because:\n")
            sys.stderr.write(f"{failed_file[2]}\n\n")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    _main()
