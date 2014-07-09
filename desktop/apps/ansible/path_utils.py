#!/usr/bin/env python

import os
import logging
import shutil

from django.conf import settings

LOG = logging.getLogger(__name__)

#  /desktop
#   ext
#   projects
#      inventories
#      playbooks
#      vars
#      resources
#
# #####


def get_real_dir(f):
    return os.path.realpath(f)

def ensure_dir(f):
    d = get_real_dir(f)
    if not os.path.exists(d):
        os.makedirs(d,mode=0755)
def delete_dir(f):
    try:
        shutil.rmtree(f)
    except:
        LOG.error('rm Error')

def ensure_project_tmp_dir(project_name):
    ensure_dir(get_project_dir(project_name))
    p = get_project_dir(project_name)
    p = os.path.join(p,".tmp")
    ensure_dir(p)



#Credential
def get_credential_dir(user):
    return get_real_dir(os.path.join(settings.ACCOUNT_PROFILE_ROOT, user))

def ensure_credential_dir(user):
    ensure_dir(get_credential_dir(user))

def create_credential_file(user, ssh_key):
    ensure_credential_dir(user)
    file_path =os.path.join(get_credential_dir(user),"id_dsa")
    f=file(file_path, "w+")
    f.writelines(ssh_key)
    f.flush()
    f.close()
    return file_path


#Project vice
def get_project_dir(project_name):
    return get_real_dir(os.path.join(settings.ANSIBLE_PROJECTS_ROOT, project_name))

def get_project_file_content(project_name, p):
    path = p.encode('utf-8')
    content=""
    if os.path.exists(path):
        try:
            obj = open(path, 'r')
            for l in obj:
                content += l
            obj.close()
        except IOError, e:
            LOG.error('open file [%s] error:' % path)
    return content

def ensure_project_dir(project_name):
    ensure_dir(get_project_dir(project_name))
    ensure_inventories_dir(project_name)
    ensure_playbooks_dir(project_name)
    ensure_vars_dir(project_name)
    ensure_packages_dir(project_name)
    ensure_data_dir(project_name)
def delete_project_dir(project_name):
    p=get_project_dir(project_name)
    delete_dir(p)


#Script vice
def create_tmp_script_file(project_name,f_name,f_content):
    ensure_project_tmp_dir(project_name)
    file_path =os.path.join(get_project_dir(project_name),".tmp",f_name)
    f=file(file_path, "w+")
    f.writelines(f_content)
    f.flush()
    f.close()
    return file_path

#Playbook vice
def get_playbooks_dir(project_name):
    return get_real_dir(os.path.join(get_project_dir(project_name), "playbooks"))

def get_playbook_local_path(project_name,playbook_name):
    playbooks_dir=get_playbooks_dir(project_name)
    return os.path.join(playbooks_dir,playbook_name)

def ensure_playbooks_dir(project_name):
    ensure_dir(get_playbooks_dir(project_name))


def create_tmp_task_file(project_name,f_name,f_content):

    ensure_project_tmp_dir(project_name)

    file_path =os.path.join(get_project_dir(project_name),".tmp",f_name)
    f=file(file_path, "w+")
    f.writelines(f_content)
    f.flush()
    f.close()
    return file_path

def get_inventories_dir(project_name):
    return get_real_dir(os.path.join(get_project_dir(project_name), "inventories"))

def ensure_inventories_dir(project_name):
    ensure_dir(get_inventories_dir(project_name))

def get_inventory_local_path(project_name,inventory_name):
    inventories_dir=get_inventories_dir(project_name)
    return os.path.join(inventories_dir,inventory_name)

def create_inventory_file(project_name,f_name,f_content):

    ensure_inventories_dir(project_name)
    f=file(os.path.join(get_inventories_dir(project_name),f_name), "w+")
    f.writelines(f_content)
    f.flush()
    f.close()

def handle_uploaded_file(f):
    destination = open('%s' %settings.TMP_FILE, "w+")
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()


def ensure_vars_dir(project_name):
    ensure_dir(get_vars_dir(project_name))

def get_vars_dir(project_name):
    return get_real_dir(os.path.join(get_project_dir(project_name), "vars"))
def get_vars_local_path(project_name,var_name):
    vars_dir=get_vars_dir(project_name)
    return os.path.join(vars_dir,var_name)


def get_packages_dir(project_name):
    return get_real_dir(os.path.join(get_project_dir(project_name), "packages"))

def ensure_packages_dir(project_name):
    ensure_dir(get_packages_dir(project_name))

def get_data_dir(project_name):
    return get_real_dir(os.path.join(get_project_dir(project_name), "data"))

def ensure_data_dir(project_name):
    ensure_dir(get_data_dir(project_name))
