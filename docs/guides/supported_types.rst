.. _my_supported_types:

Supported Types
###############

The following is a list of all Python types that are serialisable with Exprés.


Core
*****

* :class:`tuple`: A tuple is serialised into a single list with a tag, so loading files automatically return tuples.
* :class:`~uuid.UUID`: A :class:`~uuid.UUID` instance is serialised into a hexadecimal encoded string.

Qiskit
******

Qiskit objects and related data can be saved with ASDF using `asdf-qiskit
<https://github.com/conradhaupt/asdf-qiskit/>`. As an ASDF extension, it
automatically integrates into ASDF and thus Exprés.
