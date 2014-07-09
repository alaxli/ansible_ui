#!/usr/bin/env python
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import django.views.static
import django.views.generic.base
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.http import urlquote

from desktop.core.lib.django_util import render,render_json
from desktop.core.lib.exceptions import StructuredException
from desktop.core.lib.exceptions_renderable import PopupException

from django.contrib.auth import REDIRECT_FIELD_NAME

LOG = logging.getLogger(__name__)
MIDDLE_WARE_HEADER = "X-Middleware-Response"

# Views inside Django that don't require login
# (see LoginAndPermissionMiddleware)
DJANGO_VIEW_AUTH_WHITE_LIST = [
  django.views.static.serve,
  django.views.generic.base.RedirectView,
]


class ExceptionMiddleware(object):
  def process_exception(self, request, exception):


    import traceback
    tb = traceback.format_exc()

    if isinstance(exception, PopupException):
        return exception.response(request)

    if isinstance(exception, StructuredException):
      if request.ajax:
        response = render_json(exception.response_data)
        response[MIDDLE_WARE_HEADER] = 'EXCEPTION'
        response.status_code = getattr(exception, 'error_code', 500)
        return response
      else:
        response = render("error.html", request,dict(error=exception.response_data.get("message")))
        response.status_code = getattr(exception, 'error_code', 500)
        return response

    return None

class AjaxMiddleware(object):
    """
    Middleware that augments request to set request.ajax
    for either is_ajax() (looks at HTTP headers) or ?format=json
    GET parameters.
    """
    def process_request(self, request):
        request.ajax = request.is_ajax() or request.REQUEST.get("format", "") == "json"
        return None

class LoginAndPermissionMiddleware(object):
  def process_view(self, request, view_func, view_args, view_kwargs):

    # If the view has "opted out" of login required, skip
    if hasattr(view_func, "login_not_required"):
        return None

    # There are certain django views which are also opt-out, but
    # it would be evil to go add attributes to them
    if view_func in DJANGO_VIEW_AUTH_WHITE_LIST:
       return None

    if request.user.is_active and request.user.is_authenticated():
        return None

    if request.ajax:
      # Send back a magic header which causes Hue.Request to interpose itself
      # in the ajax request and make the user login before resubmitting the
      # request.
      response = HttpResponse("/* login required */", content_type="text/javascript")
      response[MIDDLE_WARE_HEADER] = 'LOGIN_REQUIRED'
      return response
    else:
      return HttpResponseRedirect("%s?%s=%s" % (settings.LOGIN_URL, REDIRECT_FIELD_NAME, urlquote(request.get_full_path())))


