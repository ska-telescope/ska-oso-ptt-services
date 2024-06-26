"""Configuration file for Sphinx."""
import os
import sys
 
sys.path.insert(0, os.path.abspath("../../src"))
 
project = "ska-oso-ptt-services"
copyright = "2024, SKAO"
author = "Team Nakshatra"
release = "1.0.0"
 
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]
 
exclude_patterns = []
 
html_css_files = [
    'css/custom.css',
]
 
html_theme = "ska_ser_sphinx_theme"
html_theme_options = {}
 
 
intersphinx_mapping = {'python': ('https://docs.python.org/3.10', None)}
 
nitpicky = True