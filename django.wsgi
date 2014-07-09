# -*- coding: utf-8 -*-
import os
import sys
import site

site.addsitedir('/yourvirtualenv/lib64/python2.6/site-packages')
site.addsitedir('/yourvirtualenv/lib/python2.6/site-packages/')

activate_env = os.path.expanduser('/yourvirtualenv/bin/activate_this.py')
execfile(activate_env, dict(__file__ = activate_env))

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

current_dir = os.path.dirname(__file__)
if current_dir not in sys.path: sys.path.append(current_dir) 
os.environ['DJANGO_SETTINGS_MODULE'] = 'desktop.core.settings'


import djcelery
djcelery.setup_loader()

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
