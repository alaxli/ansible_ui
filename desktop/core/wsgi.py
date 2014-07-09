# -*- coding: utf-8 -*-
import os
import sys
import djcelery
djcelery.setup_loader()
os.environ['DJANGO_SETTINGS_MODULE'] = 'desktop.core.settings'
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path: sys.path.append(current_dir) 
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
