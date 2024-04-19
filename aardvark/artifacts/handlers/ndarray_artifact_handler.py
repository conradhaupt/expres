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

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from aardvark.artifacts.handlers.base_artifact_handler import BaseArtifactHandler
from aardvark.artifacts.typing import ArtifactFormat


class NDArrayArtifactHandler(BaseArtifactHandler):
    """Artifact handler for numpy arrays.

    Files are saved using :fun:`numpy.savez_compressed`.
    """

    @property
    def format(self) -> ArtifactFormat:
        return "npz"

    @classmethod
    def source_for(cls, attr: str) -> str:
        return "{}.npz".format(attr)

    def save_obj_to(self, obj: Any, path: Path):
        """Save ``obj`` to a ``.npz`` file at ``path``.

        Args:
            obj: The object to save. Must be an instance of
                :class:`numpy.ndarray`.
            path: The path to the file into which ``obj`` is saved.

        Raises:
            ValueError: If ``obj`` is not an instance of :class:`numpy.ndarray`.
            RuntimeError: If saving to ``path`` failed.
        """
        if not isinstance(obj, np.ndarray):
            raise ValueError(
                "{} cannot save object of type {}.".format(
                    self.__class__.__name__, type(obj).__name__
                )
            )

        try:
            with open(path, "wb") as f:
                np.savez_compressed(f, obj=obj, allow_pickle=False)
        except Exception as e:
            raise RuntimeError("Failed to save NDArray.") from e

    def load_obj_from(self, path: Path) -> npt.ArrayLike:
        """Load a numpy array from the file at ``path``.

        Args:
            path: The path to a ``.npz`` file.

        Raises:
            RuntimeError: If loading the array failed.

        Returns:
            The numpy array stored in the file at ``path``.
        """
        try:
            with np.load(
                path,
                allow_pickle=False,
            ) as _npz:
                obj = _npz["obj"]
        except Exception as e:
            raise RuntimeError(
                "Failed to load NDArray from path {}.".format(path)
            ) from e
        return obj
