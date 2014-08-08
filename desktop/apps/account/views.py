'''
modules for account app
'''
try:
    import json
except:
    import simplejson as json

from django.contrib.auth.models import User, Group
from desktop.core.lib.django_util import render
from desktop.core.lib.exceptions_renderable import PopupException
from desktop.apps.account.models import Profile
from desktop.apps.account.crypt import AESencrypt

def list_users(request):
    ''' list users '''
    users_json = json.dumps(list(User.objects.values_list('id', flat=True)))
    return render("account/list_users.html", request ,{
            'login_user':request.user,
            'users': User.objects.all(),
            'users_json': users_json,
            'request': request,
           })

def delete_user(request, username):
    ''' delete user '''
    return render("account/list_users.html",request,{})


def profile(request, username):
    ''' user's profile '''
    view_user = User.objects.get(username = username)
    profile = None
    if request.method == 'POST':
        cn_name = request.POST.get('cn')
        phonenum = request.POST.get('phone')
        profile = Profile.objects.get_or_create(user=request.user)[0]
        profile.cn_name = cn_name
        profile.phonenum = phonenum
        profile.save()
    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = None
    if profile == None:
        try:
            profile = Profile.objects.get(user=view_user)
        except:
            pass
    return render("account/profile.html", request, {
        'login_user':request.user,
        'username':username,
        'view_user':view_user,
        'profile':profile,
        })

def credential(request, username):
    ''' user's credential , for ansible jobs '''
    user = User.objects.get(username = username)
    if (request.user != user):
        raise PopupException('Sorry, you have not right to see the cretential!')

    if request.method == 'POST':
        ssh_password = request.POST.get('ssh_password')
        ssh_key = request.POST.get('id_dsa_pub')
        profile = Profile.objects.get_or_create(user=request.user)[0]
        if ssh_password == '':
            profile.ssh_password=''
        else:
            profile.ssh_password =  AESencrypt("pass34",ssh_password)        
        profile.ssh_key = ssh_key
        profile.save()

    try:
        profile = Profile.objects.get(user=request.user)
    except:
        profile = None
    return render("account/credential.html", request, {
        'username':username,
        'profile':profile,
    })

def add_ldap_users(request):
    return render("account/list_users.html", request, {})

def sync_ldap_users_groups(request):
    return render("account/list_users.html", request, {})
