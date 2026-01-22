# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'mixinforge'
copyright = '2025-2026 Vlad (Volodymyr) Pavlov'
author = 'Vlad (Volodymyr) Pavlov'

sys.path.insert(0, os.path.abspath('../../src'))

# Version from package
from mixinforge import __version__  # noqa: E402
version = release = __version__


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',        # Auto-generate from docstrings
    'sphinx.ext.napoleon',       # Google-style docstrings
    'sphinx.ext.viewcode',       # Source code links
    'sphinx.ext.intersphinx',    # Cross-project links
    'sphinx.ext.autosummary',    # Summary tables
    'sphinx_autodoc_typehints',  # Type hint rendering
    'sphinx_copybutton',         # Copy buttons for code
    'myst_parser',               # Markdown support
]

templates_path = ['_templates']
exclude_patterns = []

# -- Autodoc configuration ---------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# -- Napoleon configuration --------------------------------------------------
# Google-style docstrings (as per docstrings_comments.md)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = True

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Type hints configuration ------------------------------------------------
# Conventions in type_hints.md
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_theme_options = {
    'show_nav_level': 2,
    'navigation_depth': 4,
    'show_toc_level': 2,
    'navbar_align': 'left',
    'github_url': 'https://github.com/pythagoras-dev/mixinforge',
    'logo': {
        'text': 'mixinforge',
    },
    'footer_start': ['copyright'],
    'footer_end': ['sphinx-version', 'theme-version'],
}
html_static_path = ['_static']
html_title = f'{project} v{version}'
html_short_title = project
html_favicon = None  # Add favicon later if needed
html_show_sourcelink = True
html_copy_source = True
