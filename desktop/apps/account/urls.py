'''
urls for ansible app
'''
from django.conf.urls import patterns, url
from desktop.core.lib.django_util import get_name_re_rule

name_re = get_name_re_rule()


urlpatterns = patterns('desktop.apps.account.views',
    url(r'^$', 'list_users'),
    url(r'^users$', 'list_users'),
    url(r'^users/profile/(?P<username>%s)$' % (name_re,), 
        'profile',name='profile'),
    url(r'^users/credential/(?P<username>%s)$' % (name_re,),
        'credential',name='credential'),
    url(r'^users/delete/(?P<username>%s)$' % (name_re,), 
        'delete_user',name='delete_user'),
    url(r'^users/add_ldap_users$', 'add_ldap_users',name='add_ldap_users'),
    url(r'^users/sync_ldap_users_groups$', 
        'sync_ldap_users_groups',name='sync_ldap_users_groups'),

)

