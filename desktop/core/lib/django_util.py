import simplejson

from django.conf import settings
from django.http import  HttpResponse
from django.shortcuts import render_to_response as django_render_to_response
from django.template import RequestContext


NAME_RE_RULE = "[^-:\s][^:\s]*"
DESC_RE_RULE = "[\w-]+"
ID_RE_RULE = "[\d-]+"

def get_name_re_rule():
    return NAME_RE_RULE

def get_desc_re_rule():
    return DESC_RE_RULE

def get_id_re_rule():
    return ID_RE_RULE


def login_not_required(func):
  func.login_not_required = True
  return func

def render(template, request, data, **kwargs):
    return django_render_to_response(template,RequestContext(request=request, dict_=data), **kwargs)

def render_json(data):
    if settings.DEBUG:
        indent = 2
    else:
        indent = 0
    json = simplejson.dumps(data, indent)

    return HttpResponse(json, mimetype='application/json')




