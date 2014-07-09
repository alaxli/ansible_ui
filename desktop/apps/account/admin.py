'''
this module register profile of user to admin
'''
#!/usr/bin/python
# -*- coding : utf-8 -*-

from django.contrib import admin
from desktop.apps.account.models import Profile

class ProfileAdmin(admin.ModelAdmin):
    """docstring for AuthorAdmin"""
    list_display = ('cn_name', 'ssh_password', 'ssh_key', 'phonenum')


admin.site.register(Profile, ProfileAdmin)
