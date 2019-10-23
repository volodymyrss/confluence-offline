from setuptools import setup
import ast
import sys

setup_requires = ['setuptools >= 30.3.0', 'setuptools-git-version']
if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires.append('pytest-runner')

# Get docstring and version without importing module
with open('coff/__init__.py') as f:
    mod = ast.parse(f.read())

__doc__ = ast.get_docstring(mod)
__version__ = mod.body[-1].value.s

setup(description=__doc__.splitlines()[1],
      long_description=__doc__,
      version_format = '{tag}.dev{commitcount}+{gitsha}', 
      setup_requires=setup_requires)
