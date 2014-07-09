from desktop.apps.ansible.models import *
from desktop.apps.ansible.path_utils import *
import random
import cStringIO
import logging
import os
import select
import subprocess
import time
import traceback
from celery import Task
from django.conf import settings
import pexpect
from desktop.apps.ansible.tasks import *

#job_pk=init_job()
#start_job(job_pk)

def init_project(name):
    project=Project(name=name)
    project.save()
    #ensure_project_dir(project.name)

def init_job():
    project_name="demo"

    project =Project.objects.get(name=project_name)
    playbook= get_playbook_local_path(project_name,"echo.yml")
    inventory =get_inventory_local_path(project_name,"hosts")

    print playbook

    print inventory




    job=Job()
    job.name=random.random()
    job.project=project
    job.inventory=inventory
    job.playbook=playbook
    job.save()

    return job.pk

def start_job(job_pk):
    job=Job.objects.get(pk=job_pk)
    job.start()
#    run_job=RunJob()
#    run_job.run(job_pk)






