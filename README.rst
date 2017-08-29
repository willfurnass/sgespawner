sgespawner
==========

A Sun Grid Engine (SGE) Spawner_ for JupyterHub_.

Designed to work with JupyterHub 0.7.2 but may work with more recent versions too.

Installation and usage
----------------------

#. Install ``sgespawner`` into the same Python environment as JupyterHub using e.g. ``pip install /path/to/sge/clone``
#. Make several changes to your main JupyterHub config file (which might be ``/etc/jupyterhub/jupyterhub.py``):

    #. Tell JupyterHub to use ``sgespawner`` to spawn single-user Jupyter servers (and remove any conflicting ``spawner_class`` lines): ::

        c.JupyterHub.spawner_class = 'sgespawner.SGESpawner'

    #. Ensure that the environment variables needed to submit SGE jobs (using ``qsub``) are defined: ::

        c.Spawner.sge_env = {'SGE_ROOT': '/usr/local/sge/live',
                             'SGE_CELL': 'default',
                             'SGE_CLUSTER_NAME': 'myclustername'}

    #. Provide the path to the (Jinja2_) template used to define the SGE batch jobs that start single-user Jupyter servers: ::

        c.Spawner.sge_template = '/etc/jupyterhub/jupyterhub.sge.j2'

#. Tailor the Jinja2 template to meet your needs.  The only requirements are the lines containing ``working_dir`` and ``jh_args`` shown in the following example.
   Here JupyterHub has been installed in a virtualenv_ that must be ``activate``d before use.
   In addition, SGE is told to ``j``oin the standard output and error output log files and to name the created batch job ``jupyterhub``. ::

    #!/bin/bash
    #$ -j y
    #$ -wd {{ working_dir }}
    #$ -N jupyterhub

    source /usr/virtualenvs/jupyterhub/bin/activate
    python -m jupyterhub.singleuser {{ jh_args }}

Credits
-------

Currently developed and maintained by the `Research Software Engineering team`_ at the University of Sheffield.

Work funded by OpenDreamKit_, a Horizon2020_ European `Research Infrastructure`_ project (676541_) that aims to advance the open source computational mathematics ecosystem.

.. _Jinja2: https://jinja.pocoo.org/
.. _JupyterHub: https://jupyterhub.readthedocs.io/
.. _Spawner: http://jupyterhub.readthedocs.io/en/latest/spawners.html
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _Research Software Engineering team: http://rse.shef.ac.uk  
.. _Horizon2020: https://ec.europa.eu/programmes/horizon2020/
.. _Research Infrastructure: https://ec.europa.eu/programmes/horizon2020/en/h2020-section/european-research-infrastructures-including-e-infrastructures
.. _676541: http://cordis.europa.eu/project/rcn/198334_en.html
.. _OpenDreamKit: http://opendreamkit.org/

