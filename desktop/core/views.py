import logging
import sys
import traceback
import datetime
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import desktop.core.settings

from desktop.core.lib.django_util import render

LOG = logging.getLogger(__name__)

#def home(request):
#    return HttpResponseRedirect("/package/")

def log_view(request):
    l = logging.getLogger()
    return render('logs.html', request, dict(log=["No logs found!"]))

def serve_404_error(request, *args, **kwargs):
    """Registered handler for 404. We just return a simple error"""
    return render("404.html", request, dict(uri=request.build_absolute_uri()))

def serve_500_error(request, *args, **kwargs):
    """Registered handler for 500. We use the debug view to make debugging easier."""
    exc_info = sys.exc_info()
    return render("500.html", request, {'traceback': traceback.extract_tb(exc_info[2])})

def set_language(request):
    from django.utils.translation import check_for_language
#    next = request.REQUEST.get('next',None)
#    if next:
    next = request.META.get('HTTP_REFERER',None)
#    if not next:
#        next = '/'
    response = HttpResponseRedirect(next)
    if request.method == 'POST':
        lang_code = request.POST.get('language',None)
        if lang_code and check_for_language(lang_code):
            if hasattr(request,'session'):
                request.session['django_language']=lang_code
                max_age = 60*60*24*365
                expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),"%a, %d-%b-%Y %H:%M:%S GMT")
                response.set_cookie(desktop.core.settings.LANGUAGE_COOKIE_NAME,lang_code,max_age,expires)
    return response

def settings(request):
    responseContext={}
    responseContext['lang']=request.LANGUAGE_CODE
    responseContext.update(csrf(request))
    return render_to_response('settings.html',responseContext,context_instance=RequestContext(request))
