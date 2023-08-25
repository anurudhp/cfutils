# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "cfutils"
copyright = "2023, Anurudh Peduri"
author = "Anurudh Peduri"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.napoleon", "myst_parser"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

# -- HTML navigation bar -----------------------------------------------------
html_theme_options = {
    "github_user": "anurudhp",
    "github_repo": "cfutils",
    "description": "Utilities for Codeforces API and ICPCTools",
    "github_banner": "forkme.png",
    "github_type": "star",
}
html_sidebars = {
    "**": [
        "about.html",
        "localtoc.html",
        "navigation.html",
        "searchbox.html",
    ]
}
html_css_files = [
    "custom.css",
]
