#!/usr/bin/python
# -*- coding : utf-8 -*-

from django.contrib import admin
from desktop.apps.ansible.models import *
from guardian.admin import GuardedModelAdmin

class PackageAdmin(admin.ModelAdmin):
    """docstring for packageAdmin"""
    list_display = ('id','scmurl','version','date','project')
    search_fields = ('project',)

class ProjectAdmin(GuardedModelAdmin):
    """docstring for AuthorAdmin"""
    list_display = ('name','description','created_by','creation_date','active')
    search_fields = ('name',)

class JobAdmin(admin.ModelAdmin):
    """ docstring for JobAdmin """
    list_display = ('name','description','created_by','creation_date','project','status','execute_date')
    search_fields = ('project', 'status')

admin.site.register(Project,ProjectAdmin)
admin.site.register(Package,PackageAdmin)
admin.site.register(Job,JobAdmin)
