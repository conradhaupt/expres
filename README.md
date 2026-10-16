> [!CAUTION]
> Exprés is still a WIP and volatile. The library is primarily for personal use
> in our PhD research at IBM Research, Zürich, though anyone is welcome to use
> it. In its current state, we cannot guarantee there are no bugs. But our goal
> is to ensure data saved now will be loadable in future versions.

# Exprés

Exprés, the Catalan word for express, integrates Python dataclasses and
[ASDF](https://asdf.readthedocs.io/en/latest/), so that researchers can easily
save and load experimental data with [Qiskit](https://qiskit.org/) and other
scientific computing libraries in Python. Qiskit support is provided by [ASDF
Qiskit](https://github.com/conradhaupt/asdf-qiskit/), with full integration into
Exprés.

## Installation

Exprés is still under active development, but releases are published to PyPI.
You can install with your favourite Python package manager.

```bash
pip install expres
# or
uv add expres
```

To install from source, clone the GitHub repo and install with the same package
manager.

```bash
git clone git@github.com:conradhaupt/expres.git
cd expres

# With pip
pip install .

# With uv
uv add "expres @ ./"
```

## Dependencies

Exprés uses ASDF, which in-turn requires [PyYAML](https://pyyaml.org/). As
Exprés also saves figures and arrays, it depends on Matplotlib and NumPy.

## Documentation

The documentation will be hosted with Github pages soon. As the code progresses,
the documentation will be updated. The most up-to-date and extensive parts of
the docs are the guides.

# Contributing

All contributions are welcome. If you would like to test the library or
contribute more regularly, please talk to either Conrad Haupt (@conradhaupt) or
Marc Drudis (@MarcDrudis).
