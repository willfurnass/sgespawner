from setuptools import setup

setup(
    name="sgespawner",
    license="BSD",
    packages=['sgespawner'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
    ],
    install_requires=[
        'markdown',
        'jinja2',
        'jupyterhub>=0.3'
    ],
)
