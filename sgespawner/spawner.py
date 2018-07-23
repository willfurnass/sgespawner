from subprocess import Popen, PIPE, STDOUT, run

import jinja2
from tornado import gen
from traitlets import List, Unicode

from jupyterhub.utils import random_port
from jupyterhub.spawner import Spawner


__all__ = ['SGESpawner']


class SGESpawner(Spawner):

    sge_template = Unicode('', config=True,
        help="Filename of Jinja 2 template for a SGE batch job script")

    jh_env_vars_for_job = List([
        "JPY_API_TOKEN",
        "JUPYTERHUB_API_TOKEN",
        "JUPYTERHUB_CLIENT_ID",
        "JUPYTERHUB_HOST",
        "JUPYTERHUB_OAUTH_CALLBACK_URL",
        "JUPYTERHUB_USER",
        "JUPYTERHUB_API_URL",
        "JUPYTERHUB_BASE_URL",
        "JUPYTERHUB_SERVICE_PREFIX"
        ],
        config=False,
        help="JupyterHub-related environment variables to pass to SGE job")

    def __init__(self, *args, **kwargs):
        super(SGESpawner, self).__init__(*args, **kwargs)
        self.cmd_prefix = ['sudo', '-u', self.user.name]
        self.jobid = None

    def qstat_t(self, jobid, column):
        """
        Call qstat -t and extract information about a job.

        Parameters
        ----------

        jobid : `int`
            The numeric ID of the job to search for.

        column : `string`
            The name of the column to extract the information about, can be
            "host" or "state".

        Returns
        -------

        result : `string`
            The value of the column, or None if the job can not be found
        """
        qstat_columns = {'state': 4, 'host': 7}
        ret = run(self.cmd_prefix + ['qstat', '-t'],
                  stdout=PIPE, env=self.get_env())

        jobinfo = ret.stdout.decode('utf-8')

        state = None
        for line in jobinfo.split('\n'):
            line = line.strip()
            if line.startswith('{}'.format(jobid)):
                state = line.split()[qstat_columns[column]]

        return state

    def load_state(self, state):
        """Load state from the database."""
        super(SGESpawner, self).load_state(state)
        if 'jobid' in state:
            self.jobid = state['jobid']

    def get_state(self):
        """Get the current state."""
        state = super(SGESpawner, self).get_state()
        if self.jobid:
            state['jobid'] = self.jobid
        return state

    def clear_state(self):
        """Clear any state (called after shutdown)."""
        super(SGESpawner, self).clear_state()
        self.jobid = None

    @gen.coroutine
    def start(self):
        """
        Submit the (single-user Jupyter server) job to SGE and wait for it to start.

        Also stores the IP and port of the single-user server in self.user.server.

        NB you can relax the Spawner.start_timeout config value as necessary to
        ensure that the SGE job is given enough time to start.
        """
        self.user.server.port = random_port()

        # Open a (Jinja2) template for a batch job
        with open(self.sge_template, 'r') as f:
            # Instantiate the template using the username and
            # some arguments for the single-user Jupyter server process
            batch_job_submission_script = jinja2.Template(f.read()).render(
                working_dir='/home/{}'.format(self.user.name),
                jh_args=' '.join(self.get_args()),
                user_options=self.user_options)

        self.log.info("SGE: batch job sub script: '{}'".format(
            batch_job_submission_script))

        # Ensure command for submitting job run as correct user
        # by prefixing command with sudo -u <username>
        cmd = self.cmd_prefix.copy()
        # Ensure the JupyterHub API token is defined in
        # the worker session
        cmd.extend(['qsub', '-v', ','.join(self.jh_env_vars_for_job)])
        self.log.info("SGE: CMD: {}".format(cmd))

        self.proc = Popen(cmd,
                          stdout=PIPE,
                          stdin=PIPE,
                          stderr=STDOUT,
                          env=self.get_env())
        # Pipe the batch job submission script (filled-in Jinja2 template)
        # to the job submission script (saves having to create a temporary
        # file and deal with permissions)
        r = self.proc.communicate(
            input=batch_job_submission_script.encode('utf-8'))[0].decode('utf-8')
        self.log.info("SGE: {}".format(r))
        # Get the ID of the job submitted to SGE
        jid = int(r.split('Your job ')[1].split()[0])
        self.jobid = jid

        # Wait until the worker session has started
        state = self.qstat_t(jid, 'state')
        while state != 'r':
            yield gen.sleep(2.0)
            state = self.qstat_t(jid, 'state')
            self.log.info("SGE: Job State: {}".format(state))

        # Get and store the IP of the host of the worker session
        host = self.qstat_t(jid, 'host')
        host = host.split('@')[1].split('.')[0]
        self.log.info("SGE: The single user server"
                      " is running on: {}".format(host))
        self.user.server.ip = host

    @gen.coroutine
    def stop(self, now=False):
        """Stop the SGESpawner session.

        A Tornado coroutine that returns when the process has finished exiting.
        """
        if self.jobid:
            ret = Popen(self.cmd_prefix +
                        ['qdel', '{}'.format(self.jobid)],
                        env=self.get_env())
            self.log.info("SGE: {}".format(ret))

    @gen.coroutine
    def poll(self):
        """Checks if the SGESpawner session is still running.

        Returns None if it is still running and an integer exit status otherwise
        """
        if self.jobid is None:
            return 0
        state = self.qstat_t(self.jobid, 'state')
        if state:
            if state == 'r':
                # The session is running
                return None
            else:  # qw is not an option here.
                return 1
        else:
            return 0
