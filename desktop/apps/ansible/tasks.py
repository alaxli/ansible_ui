# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

import cStringIO
import logging
import os
import select
import subprocess
import time
import traceback
import MySQLdb
from celery import Task
from django.conf import settings
import pexpect
from django.core import urlresolvers
from desktop.apps.ansible.models import *
from desktop.apps.ansible.path_utils import *
from desktop.apps.account.models import Profile
from desktop.core.lib.exceptions_renderable import PopupException
from django.contrib.auth.models import User

import smtplib
from email.mime.text import MIMEText
from email.header import Header

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os.path

from threading import Thread
from Queue import Queue
from ansible.inventory import Inventory
import paramiko
import socket

LOG = logging.getLogger(__name__)

__all__ = ['RunJob']


def getfilecontent(project_name):
    path = os.path.join(settings.ANSIBLE_PROJECTS_ROOT,project_name,'inventories','hosts')
    content = ""
    if not os.path.exists(path):
        f = open(path, 'w')
        f.close()
    else:
        f = open(path)
        content = f.read()
    return content

def savefilecontent(project_name, content):
    if not content:
        return
    path = os.path.join(settings.ANSIBLE_PROJECTS_ROOT,project_name,'inventories','hosts')
    f = open(path, 'w')
    f.write(content)
    f.close()
    

def sendmail(email, status, job_pk, project_name):
    msg = MIMEText('Task is %s , please visit http://your.domain.name/ansible/%s/result/%s for detail' % (status,project_name,job_pk))

    subject = "Deploy Task Notice"
    msg['subject'] = Header(subject,'utf-8')
    
    sender= 'ansible@youremail.domain'
    receivers = email.split(',')
    msg['From'] = sender
    msg['To'] = ','.join(receivers)

    smtpObj = smtplib.SMTP('yourmail.domain')
    smtpObj.sendmail(sender, receivers, msg.as_string())
    LOG.info("Successfully send email")
    smtpObj.quit()

def get_allusers():
    allusers = User.objects.values('id','username')
    return allusers

    
def get_profile(job_pk):
    job = Job.objects.get(pk=job_pk)
    user = job.created_by
    #user = User.objects.get(username='common')
    try:
        profile = Profile.objects.get(user = user)
    except:
#        user = User.objects.get(username='common')
#        profile = Profile.objects.get(user = user)
        raise PopupException('you need to set credential, if you want to execute the task, you need to paste your  SSH Password,  SSH Pub Keys (DSA)')
    return profile

class BuildJob:

    def __init__(self, job):
        self.job = job


    def get_path_to(self, *args):
        '''
        Return absolute path relative to this file.
        '''
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def build_env(self, job, **kwargs):
        '''
        Build environment dictionary for ansible-playbook.
        '''
        env = dict(os.environ.items())
        # question: when running over CLI, generate a random ID or grab next, etc?
        # answer: TBD
        env['ANSIBLE_JOB_ID'] = str(job.pk)
        return env

    def build_args(self, job, **kwargs):

        profile = get_profile(job.pk)
        ssh_key = profile.ssh_key
        user = profile.user.username

        args = ['ansible-playbook', '-i', job.inventory]
        args.append(job.playbook)
        if job.limit:
            args.append('--limit')
            args.append(job.limit)
        if job.forks:
            args.append('-f')
            args.append(str(job.forks))
        if job.use_sudo and job.sudo_password:
            args.append('--sudo')
            args.append('--ask-sudo-pass')
        elif job.use_sudo:
            args.append('--sudo')

        args.append('--private-key')
        credential_file = create_credential_file(profile.user.username, ssh_key)
        args.append(credential_file)
        #args.append('--ask-pass')

        LOG.info(" ".join(args))



        return args

    def build_passwords(self, job, **kwargs):
        '''
        Build a dictionary of passwords for SSH private key, SSH user and sudo.
        '''
        return {}

    def build(self, **kwargs):
        args = self.build_args(self.job, **kwargs)
        cwd = get_project_dir(self.job.project.name)
        env = self.build_env(self.job, **kwargs)
        passwords = self.build_passwords(self.job, **kwargs)
        return args, cwd, env, passwords


class RunJob(Task):
    '''
    Celery task to run a job using ansible-playbook.
    '''

    name = 'run_job'

    def update_job(self, job_pk, **job_updates):
        '''
        Reload Job from database and update the given fields.
        '''
        job = Job.objects.get(pk=job_pk)
        if job_updates:
            for field, value in job_updates.items():
                setattr(job, field, value)
            job.save(update_fields=job_updates.keys())
        return job

    def run_pexpect(self, job_pk, args, cwd, env, passwords):
        '''
        Run the job using pexpect to capture output and provide passwords when
        requested.
        '''
        status, stdout, stderr = 'error', '', ''
        logfile = cStringIO.StringIO()
        logfile_pos = logfile.tell()
        child = pexpect.spawn(args[0], args[1:], cwd=cwd, env=env)
        child.logfile_read = logfile
        job_canceled = False
        while child.isalive():
            expect_list = [
                r'Enter passphrase for .*:',
                r'Bad passphrase, try again for .*:',
                r'sudo password.*:',
                r'SSH password:',
                pexpect.TIMEOUT,
                pexpect.EOF,
            ]
            result_id = child.expect(expect_list, timeout=2)
            if result_id == 0:
#                child.sendline(passwords.get('ssh_unlock_key', ''))
                profile = get_profile(job_pk)
                child.sendline(profile.ssh_password)
            elif result_id == 1:
                child.sendline('')
            elif result_id == 2:
                child.sendline(job.sudo_password)
            elif result_id == 3:
#                child.sendline(passwords.get('ssh_password', ''))
                profile = get_profile(job_pk)
                child.sendline(profile.ssh_password)
            job_updates = {}
            if logfile_pos != logfile.tell():
                job_updates['result_stdout'] = logfile.getvalue()
            job = self.update_job(job_pk, **job_updates)
            if job.cancel_flag:
                child.close(True)
                job_canceled = True
        if job_canceled:
            status = 'canceled'
        elif child.exitstatus == 0:
            status = 'successful'
        else:
            status = 'failed'
        stdout = logfile.getvalue()
        return status, stdout, stderr

    def run(self, job_pk, **kwargs):
        '''
        Run the job using ansible-playbook and capture its output.
        '''
        job = self.update_job(job_pk, status='running')
        try:
            status, stdout, stderr, tb = 'error', '', '', ''
            args, cwd, env, passwords = BuildJob(job).build()
            status, stdout, stderr = self.run_pexpect(job_pk, args, cwd, env, passwords)
        except Exception:
            tb = traceback.format_exc()
        self.update_job(job_pk, status=status, result_stdout=stdout,
                        result_stderr=stderr, result_traceback=tb)



class DeployKeyThread(Thread):
    """
    Consumer thread.  Reads hosts from the queue and deploys the
    key to them.
    """

    def __init__(self,config):
        self.config = config
        Thread.__init__(self)

    def deploy_key(self, server, config):
        prefix = "  copying key to %s@%s:%s/%s..." %(config['username'],
                                                    server,
                                                    config['ssh_dir'],
                                                    config['authorized_keys'])
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(server,
                           username=config['username'],
                           password=config['password'],
                           port=config['port'],
                           timeout=config['timeout_seconds'])
            client.exec_command('mkdir -p %s' %config['ssh_dir'])
        except socket.error:
            #print ("%s %sCONNECTION FAILURE%s" % (prefix, Fore.RED, Fore.RESET))
            return ("%s CONNECTION FAILURE" % (prefix))
            #print ("%s CONNECTION FAILURE" % (prefix))
            #return False
        except paramiko.AuthenticationException:
            #print ("%s %sAUTHENTICATION FAILURE%s" % (prefix, Fore.RED, Fore.RESET))
            return ("%s AUTHENTICATION FAILURE" % (prefix))
            #print ("%s AUTHENTICATION FAILURE" % (prefix))
            #return False
        if config['append']:
            client.exec_command('echo "%s" >> %s/%s' %(config['key'], config['ssh_dir'], config['authorized_keys']))
        else:
            client.exec_command('echo "%s" > %s/%s' %(config['key'], config['ssh_dir'], config['authorized_keys']))
        client.exec_command('chmod 644 %s/%s' % (config['ssh_dir'], config['authorized_keys']))
        client.exec_command('chmod 700 %s' %config['ssh_dir'])
        return "%s SUCCESS!" % (prefix)
        #return True

    def run(self):
        while True:
            global queue
            server = queue.get()
            result = self.deploy_key(server,self.config)
            global results
            results.append(result)
            queue.task_done()

def get_hosts(hostfile, pattern):
    hosts = []
    inventory = Inventory(hostfile)
    hosts = inventory.list_hosts(pattern)
    return hosts

def get_sshkey_deploy(hosts, user, password, key):
    config = {}
    config['username'] = user
    config['password'] = password
    config['key'] = key
    config['authorized_keys'] = "authorized_keys"
    config['ssh_dir'] = "~/.ssh" 
    config['port'] = 22
    config['timeout_seconds'] = 3
    config['threads'] = 100
    config['append'] = True

    global results
    results = []
    
    global queue 
    queue = Queue(maxsize=10*config['threads'])
    deployer_threads = []
    for i in range(config['threads']):
        deployer_thread = DeployKeyThread(config)
        deployer_thread.daemon = True
        deployer_thread.start()
        deployer_threads.append(deployer_thread)

    for host in hosts:
        queue.put(host)
    queue.join()
    return results
