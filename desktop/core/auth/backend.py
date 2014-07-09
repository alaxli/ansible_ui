#coding:utf-8
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
"""
Authentication backend classes for Desktop.

These classes should implement the interface described at:
  http://docs.djangoproject.com/en/1.0/topics/auth/#writing-an-authentication-backend

In addition, the User classes they return must support:
 - get_groups() (returns a list of strings)
 - get_home_directory() (returns None or a string)
 - has_hue_permission(action, app) -> boolean
Because Django's models are sometimes unfriendly, you'll want
User to remain a django.contrib.auth.models.User object.

In Desktop, only one authentication backend may be specified.
"""

import django.contrib.auth.backends
import logging
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.conf import settings


import ldap






LOG = logging.getLogger(__name__)

def find_or_create_user(username, password=None):
  try:
    user = User.objects.get(username=username)
    LOG.debug("Found user %s in the db" % username)
  except User.DoesNotExist:
    LOG.info("Materializing user %s in the database" % username)
    user = User(username=username)
    if password is None:
      user.set_unusable_password()
    else:
      user.set_password(password)
    user.is_superuser = True
    user.save()
  return user

class DesktopBackendBase(object):
    """
    Base class for implementing an authentication backend which authenticates
    against LDAP and sets Django group membership based on LDAP Organizational
    Unit (OU) membership.
    """
    def authenticate(self, username=None, password=None):
        """
        Attempts to bind the provided username and password to LDAP.

        A successful LDAP bind authenticates the user.
        """
        raise NotImplementedError

    def bind_ldap(self, username, password):
        """
        Implements the specific logic necessary to bind a given username and
        password to the particular LDAP server.

        Override this method for each new variety of LDAP backend.
        """
        raise NotImplementedError

    def get_or_create_user(self, username, password):
        """
        Attempts to get the user from the Django db; failing this, creates a
        django.contrib.auth.models.User from details pulled from the specific
        LDAP backend.

        Override this method for each new variety of LDAP backend.
        """
        raise NotImplementedError

    def get_user(self, user_id):
        """
        Implements the logic to retrieve a specific user from the Django db.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None



class LdapBackend(DesktopBackendBase):
    def __init__(self):
        self.result = None

    def search(self, canonical_name):
        ldap.set_option(ldap.OPT_REFERRALS,0)
        l = ldap.initialize(settings.LDAP_URL)
        l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        logging.warning(settings.BIND_USER)
        l.simple_bind_s(settings.BIND_USER,settings.BIND_PASSWORD)
        logging.warning(settings.SEARCH_DN)
        base = settings.SEARCH_DN
        scope = ldap.SCOPE_SUBTREE

        #filtered_name = ldap.filter.escape_filter_chars(canonical_name)
        filtered_name = canonical_name
        filter = 'samAccountName=%s' % filtered_name
        results = l.search_s(base, scope, filter)

        #result_objects = [LDAPSearchResult(result) for result in results]
        if results:
            self.result = results[0]
            return results[0][0]
        else:
            return results

    def bind_ldap(self, username, password):
        try:
            username = self.search(username)
        except AttributeError:
            pass

        ldap.set_option(ldap.OPT_REFERRALS,0) # DO NOT TURN THIS OFF OR SEARCH WON'T WORK!
        l = ldap.initialize(settings.LDAP_URL)
        l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        l.simple_bind_s(username,password)

        return l



    def authenticate(self,username=None,password=None):
        try:
            if len(password) == 0:
                return None
            l = self.bind_ldap(username, password)
            l.unbind_s()
            return self.get_or_create_user(username,password)

        except ImportError:
            pass
        except ldap.INVALID_CREDENTIALS:
            pass

    def get_or_create_user(self, username, password):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                result = self.result[1]

                if result.has_key('memberOf'):
                    membership = result['memberOf']
                else:
                    membership = None

                # get mobile
                if result.has_key('mobile'):
                    mobile = result['mobile']
                else:
                    mobile = None

                # get email
                if result.has_key('mail'):
                    mail = result['mail'][0]
                else:
                    mail = None

                # get display name :cn | name , mailNickname is english name
                if result.has_key('first_name'):
                    first_name = result['first_name'][0]
                else:
                    first_name = ' '

                # get surname
                if result.has_key('last_name'):
                    last_name = result['last_name'][0]
                else:
                    last_name = ' '


                user = User(username=username,first_name=first_name,last_name=last_name,email=mail)

            except Exception, e:
                return None

            user.is_staff = False
            user.is_superuser = False
            user.set_password('ldap authenticated')
            user.save()


        return user

