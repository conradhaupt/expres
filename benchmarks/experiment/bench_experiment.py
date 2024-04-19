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

from datetime import datetime_CAPI
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


def get_tree_attributes(
    instance: MockExperiment | MockDataclass,
) -> tuple[int, float, tuple[int, ...]]:
    return (instance.tree1, instance.tree2, instance.tree3)


def get_tree_attributes_mapping(
    instance: asdf.AsdfFile | dict[str, Any],
) -> tuple[int, float, tuple[int, ...]]:
    return (instance["tree1"], instance["tree2"], instance["tree3"])


def get_other_attribute(
    instance: MockExperiment | MockDataclass,
) -> float:
    return instance.property1


def set_tree_attributes(instance: MockExperiment | MockDataclass):
    instance.tree1 = 0
    instance.tree2 = -9.65876
    instance.tree3 = (9, 8, 7, 6, 5, 4, 3, 2, 1)


def set_tree_attributes_mapping(instance: asdf.AsdfFile | dict[str, Any]):
    instance["tree1"] = 0
    instance["tree2"] = -9.65876
    instance["tree3"] = (9, 8, 7, 6, 5, 4, 3, 2, 1)


def call_attributeless_method(instance: MockExperiment | MockDataclass) -> int:
    return instance.meth_int()


# *** Get a tree attribute
@pytest.mark.benchmark(group="experiment_get_tree_attribute")
def bench_get_tree_attribute_experiment(
    benchmark: BenchmarkSession, experiment: MockExperiment
):
    benchmark(get_tree_attributes, experiment)


@pytest.mark.benchmark(group="experiment_get_tree_attribute")
def bench_get_tree_attribute_dataclass(
    benchmark: BenchmarkSession, dataclass: MockDataclass
):
    benchmark(get_tree_attributes, dataclass)


@pytest.mark.benchmark(group="experiment_get_tree_attribute")
def bench_get_tree_attribute_asdf(benchmark: BenchmarkSession, tree: asdf.AsdfFile):
    benchmark(get_tree_attributes_mapping, tree)


@pytest.mark.benchmark(group="experiment_get_tree_attribute")
def bench_get_tree_attribute_dict(
    benchmark: BenchmarkSession, vanilla_dict: dict[str, Any]
):
    benchmark(get_tree_attributes_mapping, vanilla_dict)


# *** Get a non-tree attribute, such as a @property
@pytest.mark.benchmark(group="experiment_get_non_tree_attribute")
def bench_get_other_attribute_experiment(
    benchmark: BenchmarkSession, experiment: MockExperiment
):
    benchmark(get_other_attribute, experiment)


@pytest.mark.benchmark(group="experiment_get_non_tree_attribute")
def bench_get_other_attribute_dataclass(
    benchmark: BenchmarkSession, dataclass: MockDataclass
):
    benchmark(get_other_attribute, dataclass)


# *** Set a tree attribute
@pytest.mark.benchmark(group="experiment_set_tree_attribute")
def bench_set_tree_attribute_experiment(
    benchmark: BenchmarkSession, experiment: MockExperiment
):
    benchmark(set_tree_attributes, experiment)


@pytest.mark.benchmark(group="experiment_set_tree_attribute")
def bench_set_tree_attribute_dataclass(
    benchmark: BenchmarkSession, dataclass: MockDataclass
):
    benchmark(set_tree_attributes, dataclass)


@pytest.mark.benchmark(group="experiment_set_tree_attribute")
def bench_set_tree_attribute_asdf(benchmark: BenchmarkSession, tree: asdf.AsdfFile):
    benchmark(set_tree_attributes_mapping, tree)


@pytest.mark.benchmark(group="experiment_set_tree_attribute")
def bench_set_tree_attribute_dict(
    benchmark: BenchmarkSession, vanilla_dict: dict[str, Any]
):
    benchmark(set_tree_attributes_mapping, vanilla_dict)


# *** Call a function that does not use any tree or non-tree attributes
@pytest.mark.benchmark(group="experiment_call_attributeless_method")
def bench_call_attributeless_method_experiment(
    benchmark: BenchmarkSession, experiment: MockExperiment
):
    benchmark(call_attributeless_method, experiment)


@pytest.mark.benchmark(group="experiment_call_attributeless_method")
def bench_call_attributeless_method_dataclass(
    benchmark: BenchmarkSession, dataclass: MockDataclass
):
    benchmark(call_attributeless_method, dataclass)
