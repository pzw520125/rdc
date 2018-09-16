#!/usr/bin/env python
"""
DMLC submission script, local machine version
"""

import argparse
import sys
import os
import signal

import subprocess
from threading import Thread
import tracker
import signal
import logging
import libtmux

keepalive = """
nrep=0
rc=254
while [ $rc -eq 254 ];
do
    export DMLC_NUM_ATTEMPT=$nrep
    %s
    rc=$?;
    nrep=$((nrep+1));
done
"""
global launcher
launcher = None

class TmuxLauncher(object):
    def __init__(self, args, unknown):
        self.args = args
        self.cmd = ' '.join(args.command) + ' ' + ' '.join(unknown)
        self.server = libtmux.Server()
    def exec_cmd(self, cmd, window, pass_env):
        def export_env(env):
            export_str = ''
            for k, v in env.items():
                export_str += 'export %s=%s;' % (k ,v)
            return export_str
        #env = os.environ.copy()
        env = dict()
        for k, v in pass_env.items():
            env[k] = str(v)
        ntrial = 0
        export_str = export_env(env)
        export_str += ';'
        #bash = keepalive % (cmd)
        bash = cmd
        window.panes[0].send_keys(export_str)
        window.panes[0].send_keys(bash)

    def submit(self):
        def mthread_submit(nworker, envs):
            """
            customized submit script
            """
            procs = {}
            windows = dict()
            for i in range(nworker):
                if i == 0:
                    self.session = self.server.new_session(session_name='tracker')
                    window = self.session.windows[0]
                else:
                    window = self.session.new_window()
                self.exec_cmd(self.cmd, window, envs)
            self.session.attach_session()
        return mthread_submit

    def run(self):
        tracker.config_logger(self.args)
        tracker.submit(self.args.num_workers,
                       fun_submit = self.submit(),
                       pscmd = self.cmd)

def signal_handler(sig, frame):
    global launcher
    launcher.session.kill_session()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description='DMLC script to submit dmlc jobs as local process')

    parser.add_argument('-n', '--num-workers', required=True, type=int,
                        help = 'number of worker nodes to be launched')
    parser.add_argument('--log-level', default='INFO', type=str,
                        choices=['INFO', 'DEBUG'],
                        help = 'logging level')
    parser.add_argument('--log-file', type=str,
                        help = 'output log to the specific log file')
    parser.add_argument('command', nargs='+',
                        help = 'command for launching the program')
    args, unknown = parser.parse_known_args()
    signal.signal(signal.SIGINT, signal_handler)
    global launcher
    launcher = TmuxLauncher(args, unknown)
    launcher.run()
    signal.pause

if __name__ == '__main__':
    main()