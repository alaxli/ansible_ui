# Django settings for DeployPortal project.
# coding=utf-8
import os.path
import sys, os
import djcelery
from django.utils.translation import ugettext

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = '*'

DESKTOP_CORE_ROOT=os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DESKTOP_CORE_ROOT, 'apps'))

ANSIBLE_PROJECTS_ROOT = os.path.join(DESKTOP_CORE_ROOT,'..','..', 'projects')
ACCOUNT_PROFILE_ROOT = os.path.join(DESKTOP_CORE_ROOT,'..','..', 'cretential')
TMP_FILE = os.path.join(DESKTOP_CORE_ROOT, 'tmp')


ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS


#Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'zh-cn'

ugettext = lambda s:s
LANGUAGES =(
    ('en',ugettext('English')),
    ('zh-cn',ugettext('Chinese')),
)

LANGUAGE_COOKIE_NAME = 'django_language'

DEFAULT_CHARSET='utf-8'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''



# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(DESKTOP_CORE_ROOT,'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    ('css',os.path.join(STATIC_ROOT,'css').replace('\\','/') ),
    ('img',os.path.join(STATIC_ROOT,'img').replace('\\','/') ),
    ('js',os.path.join(STATIC_ROOT,'js').replace('\\','/') ),
    ('ext',os.path.join(STATIC_ROOT,'ext').replace('\\','/') ),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )

SECRET_KEY = '=po1*pncq=%-c$@3wf9b3!-(#*=pcf(1nd(p)lzat+3h9_7o2%'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request"
)
'''
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.i18n",
)'''

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'desktop.core.middleware.AjaxMiddleware',
    # Must be after Session, Auth, and Ajax.  Before everything else.
    'desktop.core.middleware.LoginAndPermissionMiddleware',
    'desktop.core.middleware.ExceptionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'desktop.core.pagination.middleware.PaginationMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware'
    )

ROOT_URLCONF = 'desktop.core.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'desktop.core.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(DESKTOP_CORE_ROOT, 'templates'),
)
LOCALE_PATHS = (
    os.path.join(DESKTOP_CORE_ROOT, 'locale' ),
)

AUTHENTICATION_BACKENDS = (
    'desktop.core.auth.backend.LdapBackend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
    )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    'desktop.core.pagination',
#    # Uncomment the next line to enable admin documentation:
#    'django.contrib.admindocs',
    'south',
    'kombu.transport.django',
    'djcelery',
    'desktop.apps.ansible',
    'desktop.apps.account',
    'guardian',
    )

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/tmp/deploy_debug.log',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
            },
        'desktop': {
            'handlers': ['file_handler'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

if 'djcelery' in INSTALLED_APPS:
    import djcelery
    djcelery.setup_loader()
BROKER_URL = 'django://'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TRACK_STARTED = True
CELERYD_TASK_TIME_LIMIT = 600
CELERYD_TASK_SOFT_TIME_LIMIT = 540
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERYBEAT_MAX_LOOP_INTERVAL = 60


ANONYMOUS_USER_ID = -1
 # User settings
from internal.settings_local import *
