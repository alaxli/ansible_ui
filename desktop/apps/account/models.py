'''
models for ansible app
'''
from django.db import models
#from django.conf import settings
from django.contrib.auth.models import User
#from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

class Profile(models.Model):
    ''' User's Profile'''
    user = models.ForeignKey(User, unique=True, verbose_name=_('user'))
    cn_name = models.CharField(_('cn_name'), 
            max_length=50, 
            null=True, 
            blank=True)
    ssh_password = models.CharField(_('ssh_password'), 
            max_length=256, 
            null=True, 
            blank=True)
    ssh_key = models.CharField(_('ssh_key'), 
            max_length=2048, 
            null=True, 
            blank=True)
    phonenum = models.CharField('phonenum', 
            max_length=50, 
            null=True, 
            blank=True)

    def __unicode__(self):
        return self.user.username

    def get_absolute_url(self):
        ''' get absolute url'''
        return ('profile_detail', None, {'username': self.user.username})
    get_absolute_url = models.permalink(get_absolute_url)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')


#def create_profile(sender, instance=None, **kwargs):
#    if instance is None:
#        return
#    profile, created = Profile.objects.get_or_create(user=instance)

#post_save.connect(create_profile, sender=User)
