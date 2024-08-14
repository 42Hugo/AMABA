import os
import sys

# Add the root directory to the sys.path
sys.path.insert(0, os.path.abspath('../../..'))

#import pneumatic_control  # Verify this import works

project = 'AMABA Doc'
copyright = '2024, ICube'
author = 'Hugo Allard'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'breathe',
    'sphinx_copybutton',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

breathe_projects = {
    "AMABA": "C:\\Users\\hugoa\\OneDrive\\Bureau\\AMABA\\Automatisation\\amaba\\amaba\\documentation\\docs\\doxygen\\xml"
}
breathe_default_project = "AMABA"

# Additional Breathe configurations
breathe_default_members = ('members', 'undoc-members')
breathe_show_define_initializer = True
breathe_show_enumvalue_initializer = True

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
