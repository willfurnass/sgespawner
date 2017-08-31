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
    author='Will Furnass',
    author_email='w.furnass@sheffield.ac.uk',
    url='https://github.com/willfurnass/sgespawner',
    license="BSD",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Topic :: Utilities',
    ],
    install_requires=[
        'markdown',
        'jinja2',
        'jupyterhub>=0.7.2'
    ],
)
