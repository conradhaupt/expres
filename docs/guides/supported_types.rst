.. _my_supported_types:

Supported Types
###############

The following is a list of all Python types that are serialisable with
`asdf-qiskit`.


Core
*****

* :class:`tuple`: A tuple is serialised into a single list with a tag, so loading files automatically return tuples.
* :class:`~uuid.UUID`: A :class:`~uuid.UUID` instance is serialised into a hexadecimal encoded string.

Qiskit
******

Serialisable Qiskit types are grouped by the Qiskit submodules in-which they are found.

Circuits
========

* :class:`~qiskit.circuit.QuantumCircuit`: Circuits are serialised as a `qiskit.qpy` bytes stream, which is encoded as an ASDF block.

Quantum Info
============

* :class:`~qiskit.quantum_info.SparsePauliOp`: A single :class:`~qiskit.quantum_info.SparsePauliOp` is serialised into a list of Paulis and coefficients. Note that phases of Paulis are absorbed into the coefficients.
* :class:`~qiskit.quantum_info.PauliList`: A PauliList is saved as either a list of strings or as symplectic arrays. Phases are also included. In the symplectic form, phases are 2-bit integers indexing the phase array ``[1, -1j, -1, 1j]``.

Primitive Containers
====================


* :class:`~qiskit.primitives.BitArray`: An instance is serialised into a packed numpy array and an integer for the number of bits.
* :class:`~qiskit.primitives.DataBin`: An instance is serialised into a mapping with the shape, as a `tuple`, and each data entry as an additional entry in said mapping. The shape is not enforced on data entries by the schema, as the shape is not always validated by :class:`~qiskit.primitives.DataBin`.
* :class:`~qiskit.primitives.PubResult`: An instance contains a single `DataBin` and a metadata dictionary. Note that currently `SamplerPubResult` is not treated differently to `PubResult`.
* :class:`~qiskit.primitives.PrimitiveResult`: An instance contains a metadata dictionary and a list of `PubResult` instances.

