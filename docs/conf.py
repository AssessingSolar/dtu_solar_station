#!/usr/bin/env python


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# import ablog


# -- Project information -----------------------------------------------------

project = "DTU Solar Station"
copyright = "2024, DTU"
# author = "Adam R. Jensen"


# -- Sphinx Options -----------------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'myst_nb',
]

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**/pandoc_ipynb/inputs/*', 'ipynb_checkpoints/*']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'pydata_sphinx_theme'
html_title = 'DTU Solar Station'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
  # "github_url": "https://github.com/assessingsolar/dtu_solar_station",
  "navbar_start": ["navbar-logo"],
  "navbar_center": ["navbar-nav"],
  "navbar_end": ["navbar-icon-links"],
  "navbar_persistent": [],  # remove search button
  "secondary_sidebar_items": [],  # empty right sidebar
  "show_prev_next": False,  # hide "next section" buttons
  "footer_start": ["copyright"],
  "footer_end": [],  # don't show theme version
  "content_footer_items": ["last-updated"],  # show last updated
}

# Remove primary side bar from all pages
html_sidebars = {
  "**": []
}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = '_static/favicon.ico'

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
# html_extra_path = []

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%d %B %Y'


