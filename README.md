> [!IMPORTANT]
> Aardvark is currently being renamed to Exprés (`expres`). There will not be a
> deprecation window for this, but old data will still be loadable with the
> renamed library. Additionally, this code was originally in a mono-repo with
> `asdf-qiskit`, but has been separated into a new repo. There may still be some
> mentions of `asdf-qiskit` in the docs and code during the renaming/refactor.

> [!CAUTION]
> Aardvark is still a WIP and very volatile. The library is primarily for
> personal use in our PhD research at IBM Research, Zürich, though anyone is
> welcome to use it. In its current state, it is not guaranteed that data saved
> with this version will be loadable in future versions, though we do aim for
> backwards compatibility during this time.

# Aardvark

Aardvark, a play on "artifact", integrates Python dataclasses and
[ASDF](https://asdf.readthedocs.io/en/latest/), so that researchers can easily
save and load experimental data with [Qiskit](https://qiskit.org/) and other
scientific computing libraries in Python.

## Installation

Aardvark is still under active development, but will be published to PyPI in the
near future. You can install it from source, but note that `main` is under
active development. For release versions, see the latest `release/` branch or
use the `pip install` command below:

```bash
pip install "git+ssh://git@github.com/conradhaupt/expres.git@release/0.1"
```

## Dependencies

Aardvark uses ASDF, which in-turn requires [PyYAML](https://pyyaml.org/). As
Aardvark also saves figures and arrays, it depends on Matplotlib and NumPy.

## Documentation

The documentation will be hosted with Github pages soon. As the code progresses,
the documentation will be updated. The most up-to-date and extensive parts of
the docs are the guides.

# Contributing

All contributions are welcome. If you would like to test the library or
contribute more regularly, please talk to either Conrad Haupt (@conradhaupt) or
Marc Drudis (@MarcDrudis).
