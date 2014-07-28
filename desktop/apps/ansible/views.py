# -*- coding : utf-8 -*-
'''
This module provides main content of ansible
'''
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


from django.http import HttpResponseRedirect,HttpResponse
from desktop.apps.ansible.models import *
from desktop.apps.ansible.tasks import get_allusers
from desktop.apps.ansible.tasks import sendmail,getfilecontent,savefilecontent
from desktop.apps.ansible.tasks import get_hosts,get_sshkey_deploy
from desktop.core.lib.django_util import render,render_json
from desktop.core.lib.exceptions_renderable import PopupException
from guardian.decorators import permission_required_or_403
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from guardian.shortcuts import get_users_with_perms,get_perms
from guardian.shortcuts import assign_perm,remove_perm
from django.utils.datastructures import SortedDict
from django.db.models import Max


from django.core import urlresolvers
from django.conf import settings
import time,uuid,datetime
import re
import os
import ntpath
import logging
import simplejson as json


LOG = logging.getLogger(__name__)


#Job Vice

def execute_script(request,project_name):
    project=Project.objects.get(name=project_name)
    if request.method == 'POST':

        inventory = request.POST.get('inventory')
        script = request.POST.get('script')
        args = request.POST.get('args')
        hosts = request.POST.get('hosts')
        user = request.POST.get('user')
        use_sudo = request.POST.get('use_sudo')
        forks = request.POST.get('forks')
        limit = request.POST.get('limit')
        sudo_password = request.POST.get('sudo_password')

        script_file_name = "%s.sh" % uuid.uuid1()
        script_content = script
        script_path = create_tmp_script_file(project_name,script_file_name,script_content)

        file_name = "%s.yml" % uuid.uuid1()
        file_content  = "- hosts  : %s \n" % hosts
        file_content += "  sudo   : yes\n"
        file_content += "  user   : %s \n" % user
        file_content += "  tasks  : \n"
        file_content += "      - name: execute script \n"
        file_content += "        action: script %s %s \n" % (script_path,args)

        file_path = create_tmp_task_file(project_name,file_name,file_content)

        now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        job = Job()
        now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        job_today_id = job.get_id()
        job.name = '-'.join(['job', now , job_today_id])
        job.created_by = request.user

        job.project = project
        job.playbook = file_path
        job.inventory = get_inventory_local_path(project_name,inventory)
        if forks:
            job.forks = forks
        if limit:
            job.limit = limit
        job.use_sudo = use_sudo
        if sudo_password:
            job.sudo_password = sudo_password

        job.save()
        job_pk=job.pk

        job.start()

        return HttpResponseRedirect(urlresolvers.reverse('job_execute_result',kwargs={'project_name':project_name,'job_pk':job_pk}))


    return render("ansible/execute_script.html",request,{
        'request': request,
        'project':project
    })

def execute_playbook(request, project_name,template_pk=None):

    project = Project.objects.get(name=project_name)
    template = JobTemplate()
    plist = list(project.package.values('version','date'))
    packagelist = []
    for item in plist:
        array = {}
        array['version'] = item['version']
        array['date'] = item['date'].strftime("%Y-%m-%d-%H:%M:%S")
        packagelist.append(array)
    package_json = json.dumps(packagelist)
    pmax = project.package.annotate().order_by('-date')[:1]

    if template_pk:
        template=JobTemplate.objects.get(pk=template_pk)


    if request.method == 'POST':

        if ( request.user.has_perm('execute_proj',project) == False ):
            raise PopupException('Soarry, you have not right to execute the project!')
        
        save = request.POST.get('save')

        inventory = request.POST.get('inventory')
        var_files = request.POST.get('var_files')
        tasks = request.POST.get('tasks')
        hosts = request.POST.get('hosts')
        user = request.POST.get('user')
        use_sudo = request.POST.get('use_sudo')
        forks = request.POST.get('forks')
        limit = request.POST.get('limit')
        extra_vars = request.POST.get('extra_vars')
        sudo_password = request.POST.get('sudo_password')
        package_version = request.POST.get('packageselect')
        email = request.POST.get('email')
        #package_file = project_name + "_" + package_version + ".tar.gz"
        timer = request.POST.get('timer')

        if inventory == '<--None-->':
            file_content = request.POST.get('hosts')
            if file_content.count(','):
                file_content = '\n'.join(file_content.split(','))
            elif file_content.count(';'):
                file_content = '\n'.join(file_content.split(';'))
            else :
                file_content = '\n'.join(file_content.split(' '))
            file_name = 'hosts'
            inventory = create_tmp_task_file(project_name,file_name,file_content)

        real_tasks = ""
        for t in tasks.splitlines():
            real_tasks  = real_tasks + "     - include : " + get_playbook_local_path(project_name,t.strip()) + "\n"

        file_name = "%s.yml" % uuid.uuid1()
        file_content  = "- hosts  : %s \n" % hosts
        #file_content += "  sudo   : yes\n"
        file_content += "  user   : %s \n" % user
        if package_version == "":
            if pmax:
                package_version = str(pmax[0].version)
        if package_version != "":
            package_file = project_name + "_" + package_version + ".tar.gz"
            file_content += "  vars   :\n"
            file_content += "        package : %s \n" % package_file

        if var_files is not None and var_files !="":
            real_var_files = ""
            for f in var_files.splitlines():
                real_var_files  = real_var_files + "    - " + get_vars_local_path(project_name,f.strip()) + "\n"
            file_content += "  vars_files:\n"
            file_content += real_var_files
        file_content += "  tasks  : \n"
        file_content += real_tasks

        file_path = create_tmp_task_file(project_name,file_name,file_content)

        countdown = 0
        now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        if timer:
            execute_date = datetime.datetime.strptime(timer,"%d/%m/%Y %H:%M:%S")
            if execute_date > datetime.datetime.now():
                countdown = (execute_date - datetime.datetime.now()).seconds
        else:
            execute_date =  datetime.datetime.now()

        job = Job()

        job_today_id = job.get_id()
        job.name = '-'.join(['job', now , job_today_id])
        job.created_by = request.user

        job.project = project
        job.playbook = file_path
        job.inventory = get_inventory_local_path(project_name,inventory)
        job.extra_vars = extra_vars
        if forks:
            job.forks = forks
        if limit:
            job.limit = limit
        job.use_sudo = use_sudo
        if sudo_password:
            job.sudo_password = sudo_password
        if email != "":
            job.email = email
        job.countdown = countdown
        job.execute_date = execute_date

        job.save()
        job_pk=job.pk

        job.start()

        return HttpResponseRedirect(urlresolvers.reverse('job_execute_result',kwargs={'project_name':project_name,'job_pk':job_pk}))

    return render("ansible/execute_playbook.html",request,{
        'request': request,
        'project':project,
        'package_json':package_json,
        'template':template,
        'template_pk':template_pk,
    })

def restart_job(request,project_name,job_pk):
    user = request.user
    project=Project.objects.get(name=project_name)
    if ( user.has_perm('execute_proj',project) == False ):
        raise PopupException('Sorry, you have not right to execute the project!')
    job_current = Job.objects.get(pk = job_pk)


    now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))

    job = Job()

    job_today_id = job.get_id()
    job.name = '-'.join(['job', now , job_today_id])
    job.created_by = request.user

    job.project = project
    job.playbook = job_current.playbook
    job.inventory = job_current.inventory
    job.extra_vars = job_current.extra_vars
    job.forks = job_current.forks
    job.limit = job_current.limit
    job.email = job_current.email

    job.use_sudo = job_current.use_sudo
    job.sudo_password = job_current.sudo_password

    job.save()
    job_pk=job.pk


    job.start()
    return HttpResponseRedirect(urlresolvers.reverse('job_execute_result',kwargs={'project_name':project_name,'job_pk':job_pk}))




def delete_template(request,project_name):
    user = request.user
    project=Project.objects.get(name=project_name)
    if ( user.has_perm('config_proj',project) == False ):
        raise PopupException('Sorry, you have not right to config the project!')

    data=False
    try:
        template_pk = request.GET.get('template_pk')

        JobTemplate.objects.get(pk=template_pk).delete()
        data=True

    except Exception:
        data=False

    return render_json(data)

def save_template(request,project_name):
    user = request.user
    project=Project.objects.get(name=project_name)
    if ( user.has_perm('config_proj',project) == False ):
        raise PopupException('Sorry, you have not right to config the project!')
    if request.method == 'POST':
        template_name = request.POST.get('template_name')
        inventory = request.POST.get('inventory')
        var_file = request.POST.get('var_files')
        tasks = request.POST.get('tasks')
        hosts = request.POST.get('hosts')
        user = request.POST.get('user')
        use_sudo = request.POST.get('use_sudo')
        forks = request.POST.get('forks')
        limit = request.POST.get('limit')
        extra_vars = request.POST.get('extra_vars')
        email = request.POST.get('email')

        template_pk = request.POST.get('template_pk')

        LOG.debug("template_pk=%s" %template_pk)

        if template_pk is not None and template_pk!="None" and template_pk!="":
            template = JobTemplate.objects.get(pk = template_pk)
        else:
            template = JobTemplate()

        template.name = template_name
        template.project = project

        template.inventory = inventory

        template.playbook = tasks
        template.hosts = hosts
        template.user = user
        template.created_by = request.user
#        template.use_sudo = use_sudo
#        template.forks = forks
#        template.limit = limit
#        template.extra_vars = extra_vars
        template.vars_files = var_file
        template.email = email

        template.save()

        return HttpResponseRedirect(urlresolvers.reverse('view_project',kwargs={'project_name':project_name}))

def execute_scp(request,project_name):
    project=Project.objects.get(name=project_name)
    if request.method == 'POST':

        inventory = request.POST.get('inventory')
        hosts = request.POST.get('hosts')
        user = request.POST.get('user')
        use_sudo = request.POST.get('use_sudo')
        forks = request.POST.get('forks')
        limit = request.POST.get('limit')
        sudo_password = request.POST.get('sudo_password')
        owner = request.POST.get('owner')
        group = request.POST.get('group')
        mode = request.POST.get('mode')
        dest = request.POST.get('dest')
        file_obj = request.FILES.get('src', None)
        handle_uploaded_file(file_obj)

        script_file_name = "%s.sh" % uuid.uuid1()
        script_content = ""
        script_path = create_tmp_script_file(project_name,script_file_name,script_content)

        src_path = settings.TMP_FILE
        dest_path = dest
        file_name = "%s.yml" % uuid.uuid1()
        file_content  = "- hosts  : %s \n" % hosts
        file_content += "  user   : %s \n" % user
        file_content += "  tasks  : \n"
        file_content += "      - name: execute script \n"
        file_content += "        action: copy src=%s dest=%s owner=%s group=%s mode=%d\n" % (src_path, dest_path, owner, group, int(mode))

        file_path = create_tmp_task_file(project_name,file_name,file_content)

        now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        job = Job()
        now = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
        job_today_id = job.get_id()
        job.name = '-'.join(['job', now , job_today_id])
        job.created_by = request.user

        job.project = project
        job.playbook = file_path
        job.inventory = get_inventory_local_path(project_name,inventory)
        job.forks = forks
        if limit:
            job.limit = limit
        job.use_sudo = use_sudo
        if sudo_password:
            job.sudo_password = sudo_password

        job.save()
        job_pk=job.pk

        job.start()

        return HttpResponseRedirect(urlresolvers.reverse('job_execute_result',kwargs={'project_name':project_name,'job_pk':job_pk}))


    return render("ansible/execute_scp.html",request,{
        'request': request,
        'project':project
    })

def elfinder_view_file(request,project_name,path):
    if path[0] != '/':
        path = '/' + path
    project = Project.objects.get(name=project_name)
    content = get_project_file_content(project_name,path)
    file_name = ntpath.basename(path)
    return render("ansible/view_file.html",request,{
        'request': request,
        'path':path,
        'file_name':file_name,
        'content':content,
        'project':project,
        })

def view_file(request,project_name,path,type):
    if type.count('/') > 0:
        types = type.split('/')
        temp = '/'.join(types[1:])
        path = os.path.join(temp, path)
        type = types[0]
    project=Project.objects.get(name=project_name)
    if type == "inventory":
        path = os.path.join(get_project_dir(project_name), "inventories", path)
    if type == "playbook" :
        path = os.path.join(get_project_dir(project_name), "playbooks", path)
    if type == "vars" :
        path = os.path.join(get_project_dir(project_name), "vars", path)
    content =get_project_file_content(project_name, path)

    file_name = ntpath.basename(path)

    return render("ansible/view_file.html",request,{
        'request': request,
        'path':path,
        'file_name':file_name,
        'content':content,
        'project':project,
    })

def explore(request,project_name):
    user = request.user
    project=Project.objects.get(name=project_name)
    if ( User.objects.get(username='AnonymousUser').has_perm('config_proj',project) == False ):
        if ( user.has_perm('config_proj',project) == False ):
            raise PopupException('Sorry, you have not right to config the project!')
    return render("ansible/explore.html",request,{
        'request': request,
        'project':project
    })

def result_json(request,project_name,job_pk):
    job=Job.objects.get(pk=job_pk);
    color = re.compile('(.\[0\;\d+m)?(.*?)(.\[\dm)?')
    job.result_stdout = color.sub(r'\2', job.result_stdout)
    job.result_stderr = color.sub(r'\2', job.result_stderr)
    job.result_traceback = color.sub(r'\2', job.result_traceback)

    data = {'status':job.status,'result_stdout':job.result_stdout,'result_stderr':job.result_stderr,'result_traceback':job.result_traceback}
    if job.status == "successful" or job.status == "failed":
        if job.email != '':
            sendmail(job.email, job.status, job_pk, project_name)
    return render_json(data)

def result(request,project_name,job_pk):
    project=Project.objects.get(name=project_name)
    job=Job.objects.get(pk=job_pk);
    color = re.compile('(.\[0\;\d+m)?(.*?)(.\[\dm)?')
    job.result_stdout = color.sub(r'\2', job.result_stdout)
    job.result_stderr = color.sub(r'\2', job.result_stderr)
    job.result_traceback = color.sub(r'\2', job.result_traceback)
    return render("ansible/result.html",request,{
        'request': request,
        'job':job
        })

#TODO:PopupException
#Project Vice

def list_projects(request):
#    user=request.user
#    if  ( user.has_perm('ansible.access_ansible')==False ):
#         raise PopupException('Sorry, you have not right to manage ansible !')
    projects = Project.objects.all()
    groups = []
    for project in projects:
        if project.group not in groups and project.group != None and project.group != '':
            groups.append(project.group)

    return render("ansible/list_projects.html",request,{
        'projects': projects,
        'groups': groups,
        'request': request,
        })

def list_projects_group(request,group):
#    user=request.user
#    if  ( user.has_perm('ansible.access_ansible')==False ):
#         raise PopupException('Sorry, you have not right to manage ansible !')
    projects = Project.objects.all()
    groups = []
    for project in projects:
        if project.group not in groups and project.group != None and project.group != '':
            groups.append(project.group)
    return render("ansible/list_projects_group.html",request,{
        'projects': Project.objects.all().filter(group=group),
        'groups' : groups,
        'group' : group,
        'request': request,
        })

def delete_project(request,project_name):
    user = request.user
    project = Project.objects.get(name = project_name)
    if ( user.has_perm('manage_proj',project) == False ):
        raise PopupException('Sorry, you have not right to manage the project!')

    data=False
    try:
        Project.objects.get(name=project_name).delete()
        delete_project_dir(project_name)
        data=True

    except Exception:

        data=False

    return render_json(data)


#TODO: check the object is exists before saving
def add_project(request):
    page_errors=None

    if request.method == 'POST':
        name = request.POST.get("name")
        desc = request.POST.get("description")
        scmtype = request.POST.get("scmtype")
        scmurl = request.POST.get("scmurl")
        group = request.POST.get("group")
        if not name :
            raise Exception("project name required!")

        try:
            project=Project(name=name)
            project.description=desc
            project.created_by=request.user
            project.scmtype = scmtype
            project.scmurl = scmurl
            project.group = group
            project.save()

            ensure_project_dir(project.name)
            user = request.user
            perms = get_perms(user,project)
            if perms == []:
                assign_perm('access_proj',user,project)
                assign_perm('config_proj',user,project)
                assign_perm('execute_proj',user,project)
                assign_perm('manage_proj',user,project)

        except Exception:
            raise Exception()
        return HttpResponseRedirect(urlresolvers.reverse('list_projects'))


    return render("ansible/add_project.html",request,{
        'action': urlresolvers.reverse('add_project'),
        'page_errors':page_errors,
        'request': request,
        })

def edit_project(request,project_id=""):
    id = project_id
    user = request.user
    project = Project.objects.get(pk = id)
    if ( user.has_perm('manage_proj',project) == False ):
        raise PopupException('Sorry, you have not right to manage the project!')
    page_errors = None
    if request.method == 'POST':
        name = request.POST.get("name")
        desc = request.POST.get("description")
        scmtype = request.POST.get("scmtype")
        scmurl = request.POST.get("scmurl")
        group = request.POST.get("group")
        if not name :
            raise Exception("project name required!")
     #   project = Project.objects.get(pk = id)
        if project:
            project.name = name
            project.description = desc
            project.created_by = request.user
            project.scmtype = scmtype
            project.scmurl = scmurl
            project.group = group
            project.save()
        else:
            raise Exception("Project is not existed!")
        return HttpResponseRedirect(urlresolvers.reverse('list_projects'))
    else:
        try:
            project = Project.objects.get(id = id)
        except Exception:
            raise Http404
    return render("ansible/add_project.html",request,{
        'action': urlresolvers.reverse('edit_project',kwargs={'project_id':id}),
        'project': project,
        'page_errors':page_errors,
        'request': request,
        })

# project details & show job template
def view_project(request,project_name):
    if not project_name:
        raise Exception("project name required!")

    user = request.user
    project=Project.objects.get(name=project_name)
    if ( User.objects.get(username='AnonymousUser').has_perm('access_proj',project) == False ):
        if ( user.has_perm('access_proj',project) == False ):
            raise PopupException('Sorry, you have not right to access the project!')

    if not project:
        raise Exception("project not exits!")

    if request.method == 'POST':
        hostcontent = request.POST.get("hostcontent")
        savefilecontent(project_name, hostcontent)

    if project:
        templates = JobTemplate.objects.filter(project = project)
        hostcontent = getfilecontent(project_name)

        return render("ansible/view_project.html",request,{
            'project': project,
            'templates' : templates,
            'hostcontent' : hostcontent,
            'request': request,

            })
    else:
        return HttpResponseRedirect(urlresolvers.reverse('list_projects'))

def view_project_logs(request,project_name):
    if not project_name:
        raise Exception("project name required!")

    project=Project.objects.get(name=project_name)

    if not project:
        raise Exception("project not exits!")

    if project:
        jobs = Job.objects.filter(project = project)

        return render("ansible/view_project_logs.html",request,{
            'project': project,
            'jobs' : jobs,
            'request': request,

            })
    else:
        return HttpResponseRedirect(urlresolvers.reverse('list_projects'))

def manage_project(request,project_id=""):
    user = request.user
    id = project_id
    project = Project.objects.get(pk = id)
    if ( user.has_perm('manage_proj',project) == False ):
        raise PopupException('Sorry, you have not right to manage the project!')
    user_perms = get_users_with_perms(project,attach_perms=True)
    allusers = json.dumps(list(get_allusers()))
    page_errors = None
    if request.method == 'POST':
        for key in request.POST:
            value = request.POST[key]
        for key,value in request.POST.iteritems():
            m = re.match(r'.+_proj@',key)
            if m :
                keylist = re.split(r'@',key)
                keyperm = keylist[0]
                keyuser = User.objects.get(pk = keylist[1])
                if user_perms.has_key(keyuser):
                    if keyperm in user_perms[keyuser]:
                        user_perms[keyuser].remove(keyperm)
                    else:
                        assign_perm(keyperm,keyuser,project)
                else:
                    assign_perm(keyperm,keyuser,project)
        for key,value in user_perms.items():
            if value != []:
                for item in value:
                    remove_perm(item,key,project)
        return HttpResponseRedirect(urlresolvers.reverse('list_projects'))
    else:
        try:
            project = Project.objects.get(id = id)
        except Exception:
            raise Http404
    return render("ansible/manage_project.html",request,{
        'action': urlresolvers.reverse('manage_project',kwargs={'project_id':id}),
        'project': project,
        'user_perms' : user_perms,
        'allusers' : allusers,
        'page_errors':page_errors,
        'request': request,
        })


def deploykey(request,project_name):
    user = request.user
    project = Project.objects.get(name = project_name)
    if ( user.has_perm('manage_proj',project) == False ):
        raise PopupException('Sorry, you have not right to execute the project!')

    result = []
    page_errors = None
    if request.method == 'POST':
        inventory = request.POST.get('inventory')
        hosts = request.POST.get('hosts')
        user = request.POST.get('user')
        password = request.POST.get('password')
        key = request.POST.get('sshkey')
        
        if inventory == '<--None-->':
            file_content = hosts
            if file_content.count(','):
                file_content = '\n'.join(file_content.split(','))
            elif file_content.count(';'):
                file_content = '\n'.join(file_content.split(';'))
            else :
                file_content = '\n'.join(file_content.split(' '))
            file_name = 'hosts'
            inventory = create_tmp_task_file(project_name,file_name,file_content)
            
        inventory = get_inventory_local_path(project_name,inventory)
        hostlist = get_hosts(inventory, hosts)
        result = get_sshkey_deploy(hostlist, user, password, key)
        results = {}
        for i in range(len(result)):
            results[i] = result[i]
        results = [results]
        return render_json(results)
        
                      
    return render("ansible/deploykey.html",request,{
        'project': project,
        'result': result,
        'page_errors':page_errors,
        'request': request,
        })

def schedule(request,project_name):
    user = request.user
    project = Project.objects.get(name=project_name)
    if ( user.has_perm('execute_proj',project) == False ):
        raise PopupException('Sorry, you have not right to execute the project!')
    jobs = Job.objects.filter(project=project).filter(status='pending').exclude(countdown= 0)
    return render("ansible/schedule.html",request,{
        'project': project,
        'jobs' : jobs,
        'request': request,
        })


def delete_job(request,project_name):
    user = request.user
    project = Project.objects.get(name = project_name)
    if ( user.has_perm('execute_proj',project) == False ):
        raise PopupException('Sorry, you have not right to manage the project!')

    data=False
    try:
        job_pk = request.GET.get('job_pk')
        Job.objects.get(pk=job_pk).delete()
        data=True
    except Exception:
        data=False
    return render_json(data)
