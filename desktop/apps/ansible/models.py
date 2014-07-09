# -*- coding : utf-8 -*-
from django.conf import settings
from django.db import models, DatabaseError
from django.db.models import  SET_NULL
from django.utils.timezone import now
from jsonfield import JSONField
from djcelery.models import TaskMeta

from desktop.apps.ansible.path_utils import *
import time

# Create your models here.

PERM_INVENTORY_DEPLOY = 'run'
PERM_INVENTORY_CHECK  = 'check'

JOB_TYPE_CHOICES = [
    (PERM_INVENTORY_DEPLOY, 'Run'),
    (PERM_INVENTORY_CHECK, 'Check'),
    ]

class Package(models.Model):
    """ docstring for Package """
    version = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    scmurl = models.URLField(blank=False)

    def __unicode__(self):
        return u'%s' % (self.id)

class PrimordialModel(models.Model):
    '''
    must use a subclass CommonModel or CommonModelNameNotUnique though
    as this lacks a name field.
    '''

    class Meta:
        abstract = True

    description   = models.TextField(blank=True, default='')
    created_by    = models.ForeignKey('auth.User', on_delete=SET_NULL, null=True, related_name='%s(class)s_created', editable=False) # not blank=False on purpose for admin!
    creation_date = models.DateTimeField(auto_now_add=True)
    #tags          = models.ManyToManyField('Tag', related_name='%(class)s_by_tag', blank=True)
    #audit_trail   = models.ManyToManyField('AuditTrail', related_name='%(class)s_by_audit_trail', blank=True)
    active        = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode("%s-%s"% (self.name, self.id))

class CommonModel(PrimordialModel):
    ''' a base model where the name is unique '''

    class Meta:
        abstract = True

    name = models.CharField(max_length=128, unique=True)

class CommonModelNameNotUnique(PrimordialModel):
    ''' a base model where the name is not unique '''

    class Meta:
        abstract = True

    name = models.CharField(max_length=128, unique=False)

class Credential(CommonModelNameNotUnique):
    '''
    A credential contains information about how to talk to a remote set of hosts
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''


    user            = models.ForeignKey('auth.User', null=True, default=None, blank=True, on_delete=SET_NULL, related_name='credentials')


    # IF ssh_key_path is SET
    #
    # STAGE 1: SSH KEY SUPPORT
    #
    # ssh-agent bash &
    # save keyfile to tempdir in /var/tmp (permissions guarded)
    # ssh-add path-to-keydata
    # key could locked or unlocked, so use 'expect like' code to enter it at the prompt
    #    if key is locked:
    #       if ssh_key_unlock is provided provide key password
    #       if not provided, FAIL
    #
    # ssh_username if set corresponds to -u on ansible-playbook, if unset -u root
    #
    # STAGE 2:
    # OR if ssh_password is set instead, do not use SSH agent
    #    set ANSIBLE_SSH_PASSWORD
    #
    # STAGE 3:
    #
    # MICHAEL: modify ansible/ansible-playbook such that
    # if ANSIBLE_PASSWORD or ANSIBLE_SUDO_PASSWORD is set
    # you do not have to use --ask-pass and --ask-sudo-pass, so we don't have to do interactive
    # stuff with that.
    #
    # ansible-playbook foo.yml ...

    ssh_username = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name='SSH username',

    )
    ssh_password = models.CharField(
        blank=True,
        default='',
        max_length=1024,
        verbose_name='SSH password',

    )
    ssh_key_data = models.TextField(
        blank=True,
        default='',
        verbose_name='SSH private key',

    )
    ssh_key_unlock = models.CharField(
        max_length=1024,
        blank=True,
        default='',
        verbose_name='SSH key unlock',

    )
    sudo_username = models.CharField(
        max_length=1024,
        blank=True,
        default='',

    )
    sudo_password = models.CharField(
        max_length=1024,
        blank=True,
        default='',

    )

    @property
    def needs_ssh_password(self):
        return not self.ssh_key_data and self.ssh_password == 'ASK'

    @property
    def needs_ssh_key_unlock(self):
        return 'ENCRYPTED' in self.ssh_key_data and\
               (not self.ssh_key_unlock or self.ssh_key_unlock == 'ASK')

    @property
    def needs_sudo_password(self):
        return self.sudo_password == 'ASK'


class JobTemplate(CommonModel):
    '''
    A job template is a reusable job definition for applying a project (with
    playbook) to an inventory source with a given credential.
    '''

    project = models.ForeignKey(
        'Project',
        related_name='job_templates',
        null=True,
        on_delete=models.SET_NULL,
    )
    playbook = models.CharField(
        max_length=1024,
        default='',
    )
    inventory = models.CharField(
        max_length=1024,
        default='',
    )
    hosts = models.CharField(
        max_length=1024,
        default='',
    )
    user = models.CharField(
        max_length=1024,
        default='',
    )
    use_sudo = models.NullBooleanField(
        blank=True,
        default=None,
    )
    forks = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    limit = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    vars_files = models.TextField(
        blank=True,
        default='',

    )
    extra_vars = models.TextField(
        blank=True,
        default='',
    )
    email = models.TextField(
        blank=True,
        default='',
    )

class Project(CommonModel):
    '''
    A project represents a playbook git repo that can access a set of inventories
    '''

    # this is not part of the project, but managed with perms
    # inventories      = models.ManyToManyField('Inventory', blank=True, related_name='projects')

#    local_path = models.CharField( max_length=1024 )
    #default_playbook = models.CharField(max_length=1024)
    scmtype = models.CharField(max_length=64)
    scmurl = models.URLField(blank=True)
    package = models.ManyToManyField(Package,blank=True)
    group = models.CharField(max_length=128,null = True, blank = True)
    class Meta:
        permissions = (
            ('access_proj','Access Project'),
            ('config_proj','Config Project'),
            ('execute_proj','Execute Project'),
            ('manage_proj','Manage Project'),
        )

    @property
    def available_playbooks(self):
        playbooks = []

        import sys
        default_encoding = 'utf-8'
        if sys.getdefaultencoding() != default_encoding:
            reload(sys)
            sys.setdefaultencoding(default_encoding)
        if self.name:
            project_playbook_path = get_playbooks_dir(self.name)
            if os.path.exists(project_playbook_path):
                for dirpath,dirnames,filenames in os.walk(project_playbook_path):
                    for filename in filenames:
                        if filename.startswith("."):
                            continue
                        if os.path.splitext(filename)[-1] != '.yml':
                            continue
                        playbook = os.path.join(dirpath,filename)
                        playbook = os.path.relpath(playbook, project_playbook_path)
                        playbooks.append(playbook)
        #print sorted(playbooks)
        return sorted(playbooks)



    @property
    def available_inventories(self):
        inventories = []
        if self.name:
            project_inventories_path= get_inventories_dir(self.name)
            if os.path.exists(project_inventories_path):
                for dirpath,dirnames,filenames in os.walk(project_inventories_path.encode('utf-8')):
                    for filename in filenames:
                        inventory = os.path.join(dirpath,filename)
                        inventory = os.path.relpath(inventory, project_inventories_path)
                        inventories.append(inventory)
        return inventories

    @property
    def available_varfiles(self):
        vars_files = []
        if self.name:
            project_var_path= get_vars_dir(self.name)
            if os.path.exists(project_var_path):
                for dirpath,dirnames,filenames in os.walk(project_var_path):
                    for filename in filenames:
                        vars_file = os.path.join(dirpath,filename)
                        vars_file = os.path.relpath(vars_file, project_var_path)
                        vars_files.append(vars_file)
        return vars_files

    @property
    def available_packages(self):
        packages = []
        if self.name:
            project_packages_path= get_packages_dir(self.name)
            if os.path.exists(project_packages_path):
                for dirpath,dirnames,filenames in os.walk(project_packages_path):
                    for filename in filenames:
                        package = os.path.join(dirpath,filename)
                        package = os.path.relpath(package, project_packages_path)
                        packages.append(package)
        return packages

class Job(CommonModel):
    '''
    A job applies a project (with playbook) to an inventory source with a given
    credential.  It represents a single invocation of ansible-playbook with the
    given parameters.
    '''
    class Meta:
        ordering = ['-creation_date']
    STATUS_CHOICES = [
        ('new', 'New'),                  # Job has been created, but not started.
        ('pending', 'Pending'),          # Job has been queued, but is not yet running.
        ('running', 'Running'),          # Job is currently running.
        ('successful', 'Successful'),    # Job completed successfully.
        ('failed', 'Failed'),            # Job completed, but with failures.
        ('error', 'Error'),              # The job was unable to run.
        ('canceled', 'Canceled'),        # The job was canceled before completion.
    ]

    project = models.ForeignKey(
        'Project',
        related_name='jobs',
        null=True,
        on_delete=models.SET_NULL,
    )
    inventory = models.CharField(
        max_length=1024,
    )

    playbook = models.CharField(
        max_length=1024,
    )

    job_type = models.CharField(
        max_length=64,
        choices=JOB_TYPE_CHOICES,
    )

    credential = models.ForeignKey(
        'Credential',
        related_name='jobs',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    use_sudo = models.NullBooleanField(
        blank=True,
        default=None,
    )
    sudo_password = models.CharField(
        max_length=1024,
    )
    forks = models.PositiveIntegerField(
        blank=True,
        default=0,
    )
    limit = models.CharField(
        max_length=1024,
        blank=True,
        default='',
    )
    vars_files = models.TextField(
        blank=True,
        default=0,
    )
    extra_vars = models.TextField(
        blank=True,
        default='',
    )
    email = models.TextField(
        blank=True,
        default='',
    )

    cancel_flag = models.BooleanField(
        blank=True,
        default=False,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        editable=False,
    )
    result_stdout = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_stderr = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    result_traceback = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        editable=False,
    )

    def get_id(self):
        today = time.strftime("%Y%m%d", time.localtime(time.time()))
        today_len = len(Job.objects.filter(name__contains = today))
        today_id = str(today_len + 1)
        if len(today_id) < 5:
            today_id = ''.join(['0' for i in range(5-len(today_id))]) + today_id
        return today_id

    @property
    def celery_task(self):
        try:
            if self.celery_task_id:
                return TaskMeta.objects.get(task_id=self.celery_task_id)
        except TaskMeta.DoesNotExist:
            pass

    def start(self, **kwargs):
        from desktop.apps.ansible.tasks import RunJob, BuildJob
        if self.status != 'new':
            return False

        #username = kwargs.get('username', self.username)

        opts = {}
        self.status = 'pending'
        self.save(update_fields=['status'])

        #debug the putput of command
        job = Job.objects.get(pk = self.pk)
        buildjob = BuildJob(job)
        args, cwd, env, passwords = buildjob.build()
        #print ' '.join(args)

        task_result = RunJob().delay(self.pk, **opts)
        # The TaskMeta instance in the database isn't created until the worker
        # starts processing the task, so we can only store the task ID here.
        self.celery_task_id = task_result.task_id
        self.save(update_fields=['celery_task_id'])
        return True

    def cancel(self):
        if self.status in ('pending', 'running'):
            if not self.cancel_flag:
                self.cancel_flag = True
                self.save(update_fields=['cancel_flag'])
        return self.cancel_flag

