#!/usr/bin/python
# -*- coding : utf-8 -*-

from django.contrib import admin
from desktop.apps.ansible.models import *
from guardian.admin import GuardedModelAdmin

#class PackageAdmin(admin.ModelAdmin):
class ProjectAdmin(GuardedModelAdmin):
    """docstring for AuthorAdmin"""
    list_display = ('name','description','created_by','creation_date','active')
    search_fields = ('name',)


admin.site.register(Project,ProjectAdmin)
