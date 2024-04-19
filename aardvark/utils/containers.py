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

from __future__ import annotations

from collections.abc import Iterator, Mapping, MutableMapping
from copy import deepcopy
import dataclasses
from reprlib import recursive_repr as recursive_repr
from typing import Any, NoReturn, TypeVar

# TODO: Remove typing_extensions when minimum python3.11
try:
    from typing import Self
except:
    from typing_extensions import Self


def update_nested_dictionaries(lhs: dict[Any, Any], rhs: dict[Any, Any]):
    for k in lhs.keys():
        if k in rhs:
            if isinstance(lhs[k], dict):
                update_nested_dictionaries(lhs[k], rhs[k])
            else:
                lhs[k] = rhs[k]


_T_Key = TypeVar("_T_Key")
_T_Value = TypeVar("_T_Value")


class NoItem:
    """Dummy class to indicate that a value was not found when searching nested keys."""

    def __repr__(self) -> str:
        return "{}()".format(self.__class__.__name__)


class FrozenMappingError(AttributeError):
    pass


class NestedChainMap(MutableMapping[_T_Key, _T_Value]):
    """Nested equivalent to :class:`collections.abc.ChainMap`.


    Like ChainMap, NestedChainMap returns values based on an ordering of
    mappings provided. However, NestedChainMap will return a new NestedChainMap
    for subtrees where all values are mappings. If one value is not a mapping,
    then the value with the highest precedence is returned. If no mapping
    contains that key, a KeyError is raised. If all values are mappings, then a
    new NestedChainMap is returned.
    """

    def __init__(
        self,
        default_map: MutableMapping[_T_Key, _T_Value],
        *mappings: MutableMapping[_T_Key, _T_Value],
        frozen_precedence: bool = False,
    ) -> None:
        """Creates a wrapper container that returns nested mapping values from a
           list of mappings, by some precedence.

        Args:
            default_map: The default mapping, which has the lowest precedence.
            mappings: Additional mappings with increasing precedence.
            frozen_precedence: Whether the precedence is frozen. If True,
            :meth:`popparent` and :meth:`new_child` raise an error. Defaults to
            False.
        """
        self._maps: list[MutableMapping[_T_Key, _T_Value]] = [default_map, *mappings]
        self._frozen_precedence = frozen_precedence

    def __missing__(self, key: _T_Key) -> _T_Value | NoReturn:
        raise KeyError(key)

    def __getitem__(self, key: _T_Key, /) -> _T_Value:
        _nested_values = []
        _encountered_mapping = False
        _encountered_nonmapping = False
        for mapping in reversed(self._maps):
            try:
                _value = mapping[key]
                if isinstance(_value, Mapping):
                    _encountered_mapping = True
                    _nested_values.append(_value)
                else:
                    _encountered_nonmapping = True
                    _nested_values.append(_value)
            except KeyError:
                # Based on the implementation of ChainMap, we cannot use key in
                # mapping as defaultdict doesn't support that fully. Therefore,
                # we use mapping[key] which can raise a KeyError. If a KeyError
                # is caught, then we denote it has no value with a NoItem()
                _nested_values.append(NoItem())

        # We check if we encountered both mapping and non-mapping values. This
        # is not currently supported as its behaviour is not defined. We raise
        # after looping over all mappings as the code is cleaner, but this has
        # worse performance for a tall stack of mappings. If this use-case is
        # necessary in the future, this check should be moved into the loop so
        # the error can be raised earlier.
        if _encountered_mapping and _encountered_nonmapping:
            raise ValueError(
                "Encountered mapping and non-mapping values for key {!r}, which are not supported.".format(
                    key
                )
            )

        # _nested_values contains NoItems and either mappings or values. If we have
        # both mappings and values, we should already have caught this and
        # raised an error.
        if _encountered_nonmapping:
            for _val in _nested_values:
                if not isinstance(_val, NoItem):
                    return _val
        if _encountered_mapping:
            _mappings = []
            for _i_value, _value in enumerate(_nested_values):
                if isinstance(_value, NoItem):
                    if _i_value == 0:
                        # To make sure we handle setting values, we need to
                        # create an empty dictionary for the given key in the
                        # mapping with the highest precedence.
                        self._maps[-1][key] = {}
                        _mappings.append(self._maps[-1][key])
                    else:
                        _mappings.append({})
                else:
                    _mappings.append(_value)
            # As we are going down one level, we use a new NestedChainMap with
            # frozen precedence. This disables new_child and parents.
            return NestedChainMap(
                _mappings[-1],
                *reversed(_mappings[:-1]),
                frozen_precedence=True,
            )  # pyright: ignore[reportReturnType]
        return self.__missing__(key)

    def __setitem__(self, key: _T_Key, value: _T_Value, /) -> None:
        self._maps[-1][key] = value

    def get(self, key: _T_Key, default: Any = None):
        return self[key] if key in self else default

    def __len__(self) -> int:
        return len(set().union(*self._maps))

    def __iter__(self):
        return iter(dict(self))

    def __contains__(self, key: object, /) -> bool:
        return any(key in _map for _map in self._maps)

    def __bool__(self) -> bool:
        return any(self._maps)

    @recursive_repr()
    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, ", ".join(map(repr, self._maps))
        )

    @classmethod
    def fromkeys(cls, iterable: Iterator[_T_Key], value: _T_Value = None, /) -> Self:
        return cls(dict.fromkeys(iterable, value))

    def new_child(
        self, mapping: MutableMapping[_T_Key, _T_Value], **kwargs
    ) -> NestedChainMap[_T_Key, _T_Value] | NoReturn:
        """Return a new instance with ``mapping`` as the highest precedence.

        Args:
            mapping: New mapping to add.

        Raises:
            FrozenMappingError: If the instance precedence is frozen.
        """
        if self._frozen_precedence:
            raise FrozenMappingError(
                "Cannot new_child on instance with frozen precedence."
            )
        return self.__class__(self._maps[0], *self._maps[1:], mapping)

    @property
    def parents(self) -> NestedChainMap[_T_Key, _T_Value] | NoReturn:
        """Return a new mapping with the highest precedence mapping removed.

        Returns:
            A NestedChainMap with the highest precedence mapping removed.

        Raises:
            FrozenMappingError: If the instance precedence is frozen.
        """
        if self._frozen_precedence:
            raise FrozenMappingError(
                "Cannot new_child on instance with frozen precedence."
            )
        return self.__class__(self._maps[0], *self._maps[1:-1])

    def __delitem__(self, key: _T_Key, /) -> None:
        try:
            del self._maps[-1][key]
        except KeyError:
            raise KeyError("Key not found in the top mapping: {!r}".format(key))

    def popitem(self) -> tuple[_T_Key, _T_Value]:
        """Pop an item from the mapping with the highest precedence.

        Raises:
            KeyError: If the top mapping is empty.

        Returns:
            The key and value of the item popped from the mapping of highest
            precedence.
        """
        try:
            return self._maps[-1].popitem()
        except KeyError:
            raise KeyError("No keys found in top mapping.")

    def pop(self, key: _T_Key) -> _T_Value:
        """Pop an item and return its value from the mapping with the highest
           precedence.

        Args:
            key: The key of the item to pop.

        Raises:
            KeyError: If an item with that key does not exist in the mapping
                with the highest precedence.

        Returns:
            The value of the item with key ``key``.
        """
        try:
            return self._maps[-1].pop(key)
        except KeyError:
            raise KeyError("Key not found in the top mapping: {!r}".format(key))

    def clear(self) -> None:
        """Calls clear on the mapping with the highest precedence."""
        self._maps[-1].clear()

    # TODO: Figure out how to return a KeysView instead of a list.
    def keys(self) -> list[_T_Key]:
        """List of keys for the entire nested chain map, over all mappings.

        Returns:
            List of keys.
        """
        return list(set().union(*[_map.keys() for _map in self._maps]))

    def __dict__(self) -> dict[_T_Key, _T_Value]:
        def __parse_value(
            val: _T_Value | NestedChainMap[_T_Key, _T_Value],
        ) -> _T_Value:
            # We're 'flattening' the NestedChainMap, so we convert subtrees into dictionaries too.
            if isinstance(val, NestedChainMap):
                return val.__dict__()  # pyright: ignore[reportReturnType]
            return val

        return {k: __parse_value(self[k]) for k in self.keys()}

    def copy(self) -> NestedChainMap[_T_Key, _T_Value]:
        _copied_maps = []
        for _map in self._maps:
            _copied_maps.append(deepcopy(_map))
        _other = NestedChainMap(_copied_maps[0], _copied_maps[1:])
        return _other
