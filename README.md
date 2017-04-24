# SGE Spawner

A Sun Grid Engine (SGE) [Spawner](http://jupyterhub.readthedocs.io/en/latest/spawners.html) for [JupyterHub](https://jupyterhub.readthedocs.io/).

## Installation and usage

1. Install `sgespawner` into the same Python environment as JupyterHub using e.g. `pip install /path/to/sge/clone`
1. Make several changes to your main JupyterHub config file (which might be `/etc/jupyterhub/jupyterhub.py`):
    1. Tell JupyterHub to use `sgespawner` to spawn single-user Jupyter servers (and remove any conflicting `spawner_class` lines):
        ```python
        c.JupyterHub.spawner_class = 'sgespawner.SGESpawner'
        ```

    1. Ensure that the environment variables needed to submit SGE jobs (using `qsub`) are defined:
        ```python
        c.Spawner.sge_env = {'SGE_ROOT': '/usr/local/sge/live',
                             'SGE_CELL': 'default',
                             'SGE_CLUSTER_NAME': 'myclustername'}
        ```
    1. Provide the path to the ([Jinja2](https://jinja.pocoo.org/)) template used to define the SGE batch jobs that start single-user Jupyter servers:
        ```python
        c.Spawner.sge_template = '/etc/jupyterhub/jupyterhub.sge.j2'
        ```
1. Tailor the Jinja2 template to meet your needs.  The only requirements are the lines containing `working_dir` and `jh_args` shown in the following example.
   Here JupyterHub has been installed in a [virtualenv](https://virtualenv.pypa.io/en/stable/) that must be `activate`d before use.
   In addition, SGE is told to `j`oin the standard output and error output log files and to name the created batch job `jupyterhub`.

    ```bash
    #!/bin/bash
    #$ -j y
    #$ -wd {{ working_dir }}
    #$ -N jupyterhub

    source /usr/virtualenvs/jupyterhub/bin/activate
    python -m jupyterhub.singleuser {{ jh_args }}
    ```
