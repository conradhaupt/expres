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

"""Benchmark creating an experiment and saving it to an ASDF file."""

from datetime import datetime_CAPI
from io import BytesIO
from typing import Any

import aardvark
from aardvark.utils.tests import TestCase
import asdf
import pytest
from pytest_benchmark.session import BenchmarkSession


@aardvark.dataclass
class MockExperiment(aardvark.Experiment):
    tree1: int
    tree2: float
    tree3: tuple[int, ...]

    @property
    def property1(self) -> float:
        return self.tree1 * self.tree2

    def meth_int(self) -> int:
        return 0


@aardvark.dataclass
class MockDataclass:
    tree1: int
    tree2: float
    tree3: tuple[int, ...]

    @property
    def property1(self) -> float:
        return self.tree1 * self.tree2

    def meth_int(self) -> int:
        return 0


@pytest.fixture(scope="function")
def experiment() -> MockExperiment:
    return MockExperiment(tree1=0, tree2=0.5e9, tree3=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9))


@pytest.fixture(scope="function")
def dataclass() -> MockDataclass:
    return MockDataclass(tree1=0, tree2=0.5e9, tree3=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9))


@pytest.fixture(scope="function")
def tree() -> asdf.AsdfFile:
    _tree = asdf.AsdfFile()
    _tree["tree1"] = 0
    _tree["tree2"] = 0.5e9
    _tree["tree3"] = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    return _tree


@pytest.fixture(scope="function")
def vanilla_dict() -> dict[str, Any]:
    return {
        "tree1": 0,
        "tree2": 0.5e9,
        "tree3": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    }


def set_tree_attributes(instance: MockExperiment | MockDataclass):
    instance.tree1 = 0
    instance.tree2 = -9.65876
    instance.tree3 = (9, 8, 7, 6, 5, 4, 3, 2, 1)


def set_tree_attributes_mapping(instance: asdf.AsdfFile | dict[str, Any]):
    instance["tree1"] = 0
    instance["tree2"] = -9.65876
    instance["tree3"] = (9, 8, 7, 6, 5, 4, 3, 2, 1)


def create_save_experiment(instance: MockExperiment, buff: BytesIO):
    set_tree_attributes(instance)
    instance._tree.write_to(buff)


def create_save_attributes(instance: MockDataclass, buff: BytesIO):
    set_tree_attributes(instance)
    f = asdf.AsdfFile()
    f._tree.update(instance.__dict__)
    f.write_to(buff)


def create_save_mapping(instance: dict[str, Any], buff: BytesIO):
    set_tree_attributes_mapping(instance)
    f = asdf.AsdfFile()
    f._tree.update(instance)
    f.write_to(buff)


def create_save_asdf(instance: asdf.AsdfFile, buff: BytesIO):
    set_tree_attributes_mapping(instance)
    instance.write_to(buff)


# *** Get a tree attribute
@pytest.mark.benchmark(group="experiment_create_and_save_asdf")
def bench_create_save_experiment(
    benchmark: BenchmarkSession, experiment: MockExperiment
):
    benchmark(create_save_experiment, experiment, BytesIO())


@pytest.mark.benchmark(group="experiment_create_and_save_asdf")
def bench_create_save_dataclass(benchmark: BenchmarkSession, dataclass: MockDataclass):
    benchmark(create_save_attributes, dataclass, BytesIO())


@pytest.mark.benchmark(group="experiment_create_and_save_asdf")
def bench_create_save_asdf(benchmark: BenchmarkSession, tree: asdf.AsdfFile):
    benchmark(create_save_asdf, tree, BytesIO())


@pytest.mark.benchmark(group="experiment_create_and_save_asdf")
def bench_create_save_dict(benchmark: BenchmarkSession, vanilla_dict: dict[str, Any]):
    benchmark(create_save_mapping, vanilla_dict, BytesIO())
