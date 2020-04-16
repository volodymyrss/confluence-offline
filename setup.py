from setuptools import setup
import ast
import sys

setup_requires = ['setuptools >= 30.3.0']
if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires.append('pytest-runner')

# Get docstring and version without importing module
with open('coff/__init__.py') as f:
    mod = ast.parse(f.read())

__doc__ = ast.get_docstring(mod)
__version__ = mod.body[-1].value.s

setup(description=__doc__.splitlines()[1],
      long_description=__doc__,
      version = '0.1.3', 
      setup_requires=setup_requires)
