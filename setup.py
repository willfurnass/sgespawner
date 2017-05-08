from setuptools import setup
from distutils.util import convert_path

# Get version
main_ns = {}
ver_path = convert_path('sgespawner/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name='sgespawner',
    packages=['sgespawner'],
    version=main_ns['__version__'],
    license="BSD",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
    ],
    install_requires=[
        'markdown',
        'jinja2',
        'jupyterhub>=0.7.2'
    ],
)
