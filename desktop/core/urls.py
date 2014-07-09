from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

import desktop.apps.ansible.urls
import desktop.apps.account.urls

from django.contrib import admin
admin.autodiscover()

handler404 = 'desktop.core.views.serve_404_error'
handler500 = 'desktop.core.views.serve_500_error'

urlpatterns = patterns('',
#     url(r'^$', 'desktop.core.views.home', name='home'),
     url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),

    (r'^accounts/login/$', 'desktop.core.auth.views.dt_login'),
    (r'^accounts/logout/$', 'desktop.core.auth.views.dt_logout', {'next_page': '/'}),
    (r'^logs$','desktop.core.views.log_view'),
    (r'^settings$','desktop.core.views.settings'),
#    (r'^test$','desktop.core.views.test'),

    # Uncomment the admin/doc line below to enable admin documentation:
#    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
#    url(r'^i18n/',include('django.conf.urls.i18n')),
    url(r'^i18n/setlang/','desktop.core.views.set_language'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ansible/', include(desktop.apps.ansible.urls)),
    url(r'^account/', include(desktop.apps.account.urls)),


)
