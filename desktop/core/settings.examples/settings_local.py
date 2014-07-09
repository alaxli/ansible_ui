import os.path

# LDAP settings
NT4_DOMAIN = ""
LDAP_URL = "ldap://ldapserver:port"
BIND_USER = "CN=adreader,OU=xxx,OU=xxx,DC=xxx,DC=xxxx"
BIND_PASSWORD = "*****"
SEARCH_DN = "ou=xxxx,dc=xxxx,dc=xxxx"

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'datebase',                      # Or path to database file if using sqlite3.
        'USER': 'user',                      # Not used with sqlite3.
        'PASSWORD': '****',                  # Not used with sqlite3.
        'HOST': 'localhost',
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
    },
}
