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

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "Aardvark"
copyright = "2025, Conrad Haupt"
author = "Conrad Haupt"

# The full version, including alpha/beta/rc tags
release = "0.1.2"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "numpydoc",  # NumPy documentation
    "sphinx.ext.viewcode",  # Link to local code
    "sphinx.ext.autodoc",  # Automatic docs
    "sphinx.ext.autosummary",  # Automatic summaries
    "sphinx.ext.intersphinx",  # Inter-sphinx documentation links
    "sphinx_design",  # Web design help
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Language
language = "en"


# -- Extension config --------------------------------------------------------

# Numpydoc
numpydoc_show_class_members = True
numpydoc_class_members_toctree = False
numpydoc_show_inherited_class_members = False

# Autodoc
autodoc_default_options = {
    # Autodoc members
    "members": True,
    # Autodoc undocumented memebers
    "undoc-members": False,
    # Autodoc private memebers
    "private-members": True,
}
# No document TypeHints
autodoc_typehints = "none"

# Autosummary
autosummary_generate = True
autosummary_generate_overwrite = True

# # MyST
# myst_heading_anchors = 4

# Intersphinx Configuration
intersphinx_mapping = {
    "qiskit": ("https://docs.quantum.ibm.com/api/qiskit", None),
    "qiskit-ibm-runtime": (
        "https://docs.quantum.ibm.com/api/qiskit-ibm-runtime/",
        None,
    ),
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "asdf": ("https://www.asdf-format.org/projects/asdf/en/stable/", None),
}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Theme configuration -----------------------------------------------------

# Sidebar configuration

# General theme options
html_logo = "_static/logo.png"
