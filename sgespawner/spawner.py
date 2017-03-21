#import os
#import sys
import time
from subprocess import Popen, PIPE, STDOUT, run
#import tempfile

import jinja2
from tornado import gen
from traitlets import Dict, Unicode

from jupyterhub.utils import random_port
from jupyterhub.spawner import Spawner


__all__ = ['SGESpawner']


class SGESpawner(Spawner):

    sge_env = Dict({}, config=True,
                   help="Extra SGE environment variables needed to submit a job ")
    sge_template = Unicode('', config=True,
                   help="Filename of Jinja 2 template for a SGE batch job script")

    def __init__(self, *args, **kwargs):
        super(SGESpawner, self).__init__(*args, **kwargs)
        self.cmd_prefix = ['sudo', '-u', self.user.name]

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
                             stdout=PIPE, env=self.env)

        jobinfo = ret.stdout.decode('utf-8')

        state = None
        for line in jobinfo.split('\n'):
            line = line.strip()
            if line.startswith('{}'.format(jobid)):
                state = line.split()[qstat_columns[column]]

        return state

    def load_state(self, state):
        super(SGESpawner, self).load_state(state)
        if 'jobid' in state:
            self.jobid = state['jobid']

    def get_state(self):
        state = super(SGESpawner, self).get_state()
        if self.jobid:
            state['jobid'] = self.jobid
        return state

    def clear_state(self):
        super(SGESpawner, self).clear_state()
        self.jobid = None

    def _env_default(self):
        env = super(SGESpawner, self)._env_default()
        env.update(self.sge_env)

        return env

    @gen.coroutine
    def start(self):
        """
        Submit the job to the queue and wait for it to start
        """
        self.user.server.port = random_port()

        #tmpdir = os.environ['TMPDIR'] if 'TMPDIR' in os.environ else '/tmp'
        #file_descr, tmpfile = tempfile.mkstemp(dir=tmpdir, text=True)
        #with open(tmpfile, 'w') as f:
        #    f.write(jinja2.Template(self.sge_template).render(
        #        working_dir='/home/{}'.format(self.user.name),
        #        jh_args=self.get_args()))
        with open(self.sge_template, 'r') as f:
            batch_job_submission_script = jinja2.Template(f.read()).render(
                working_dir='/home/{}'.format(self.user.name),
                jh_args=' '.join(self.get_args()))
        self.log.info("SGE: batch job sub script: '{}'".format(batch_job_submission_script))
        cmd = self.cmd_prefix.copy()
        cmd.extend(['qsub',
                    '-v', 'JPY_API_TOKEN',
                    #tmpfile
                    ])
        # NOT NEEDED ANY MORE
        #            '-wd', '/home/{}'.format(self.user.name)])
        #cmd.extend([sys.executable, '-m', 'jupyterhub.singleuser'])
        #cmd.extend(self.get_args())

        self.log.info("SGE: CMD: {}".format(cmd))

        env = self.env.copy()

        #self.proc = Popen(cmd, stdin=batch_job_submission_script,
        #                             env=env, stdout=PIPE)
        #r = self.proc.stdout.read().decode('utf-8')
        self.proc = Popen(cmd,
                          stdout=PIPE,
                          stdin=PIPE,
                          stderr=STDOUT,
                          env=env)
        r = self.proc.communicate(
            input=batch_job_submission_script.encode('utf-8'))[0].decode('utf-8')
        self.log.info("SGE: {}".format(r))
        jid = int(r.split('Your job ')[1].split()[0])
        self.jobid = jid

        state = self.qstat_t(jid, 'state')
        while state != 'r':
            time.sleep(2)
            state = self.qstat_t(jid, 'state')
            self.log.info("SGE: Job State: {}".format(state))

        host = self.qstat_t(jid, 'host')
        host = host.split('@')[1].split('.')[0]
        self.log.info("SGE: The single user server"
                      " is running on: {}".format(host))
        self.user.server.ip = host

    @gen.coroutine
    def stop(self, now=False):
        if self.jobid:
            ret = Popen(self.cmd_prefix +
                        ['qdel', '{}'.format(self.jobid)],
                        env=self.env)
            self.log.info("SGE: {}".format(ret))

    @gen.coroutine
    def poll(self):
        state = self.qstat_t(self.jobid, 'state')
        if state:
            if state == 'r':
                return None
            else:  # qw is not an option here.
                return 1
        else:
            return 0
