# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import site
import sphinx_rtd_theme

site.addsitedir(os.path.abspath(os.path.join('.', '..', '..', 'python')))
print(os.path.abspath(os.path.join('.', '..', '..', 'python')))

from capital_analyzer import __version__, __release__

"""
VERY IMPORTANT LINES!!! Always add these, so the basic modules like numpy, Qt, ... can be loaded!!!
One of the entries is required so that import of numpy is possible, but i do not know
which one exactly. These paths are automatically added by spyder, hence it
should be no problem to add them here.
"""


f_path_conda = r"C:\ProgramData\Anaconda3"
name_env = "spyder3"
f_path_env = os.path.join(f_path_conda, "envs", name_env)

path = os.environ['PATH']

paths_to_add = []
paths_to_add.append(f_path_env)
paths_to_add.append(os.path.join(f_path_env, r'Library\mingw-w64\bin'))
paths_to_add.append(os.path.join(f_path_env, r'Library\usr\bin'))
paths_to_add.append(os.path.join(f_path_env, r'Library\bin'))
paths_to_add.append(os.path.join(f_path_env, r'Library\lib')) # this is required for PyQt
paths_to_add.append(os.path.join(f_path_env, r'Scripts'))
paths_to_add.append(os.path.join(f_path_env, r'bin'))
paths_to_add.append(os.path.join(f_path_conda, r'condabin'))
paths_to_add.append(os.path.join(f_path_conda))
paths_to_add.append(os.path.join(f_path_conda, r'Library\mingw-w64\bin'))
paths_to_add.append(os.path.join(f_path_conda, r'Library\usr\bin'))
paths_to_add.append(os.path.join(f_path_conda, r'Library\bin'))
paths_to_add.append(os.path.join(f_path_conda, r'Scripts'))

# convert to path syntax
path_tmp = (len(paths_to_add)*"{};").format(*paths_to_add)

# add to existing path variable
path = path_tmp + ';' + path
os.environ['PATH'] = path

# -- Project information -----------------------------------------------------

project = 'Capital Analyzer'
copyright = '2022, Andriy Prots'
author = 'Andriy Prots'

# The short X.Y version.
version = __version__
# The full version, including alpha/beta/rc tags.
release = __release__


# -- General configuration ---------------------------------------------------

def setup(app):
    app.add_css_file("custom.css")

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx_math_dollar', 
              'sphinx.ext.mathjax',
              'sphinx_rtd_theme'
]

mathjax_config = {
    'tex2jax': {
        'inlineMath': [ ["\\(","\\)"] ],
        'displayMath': [["\\[","\\]"] ],
    },
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
#source_suffix = '.rst'

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
'papersize': 'a4paper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',

# Latex figure (float) alignment
#'figure_align': 'htbp',
}

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


latex_docclass = {
   'howto': 'scrreprt',
   'manual': 'scrreprt',
}


