import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Nasdaq Protocols Python Library'
copyright = 'Copyright (c) 2024 Nasdaq'
author = 'Sam Daniel Thangarajan'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
extensions = ['sphinx.ext.autodoc',]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'show-inheritance': True,
}
autodoc_typehints = 'description'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# https://www.sphinx-doc.org/en/master/usage/theming.html [themes]
html_theme = 'agogo'
