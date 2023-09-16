from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

import logging

# Define logger for this file
logger = logging.getLogger(__name__)


class DanceRole(models.Model):
    '''
    Most typically for partnered dances, this will be only Lead and Follow.
    However, it can be generalized to other roles readily, or roles can be
    effectively disabled by simply creating a single role such as "Student."
    '''

    name = models.CharField(_('Name'), max_length=50, unique=True)
    pluralName = models.CharField(
        _('Plural of name'), max_length=50, unique=True,
        help_text=_('For the registration form.')
    )
    order = models.FloatField(
        _('Order number'),
        help_text=_('Lower numbers show up first when registering.')
    )

    def save(self, *args, **kwargs):
        ''' Just add "s" if no plural name given. '''

        if not self.pluralName:
            self.pluralName = self.name + 's'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Dance role')
        verbose_name_plural = _('Dance roles')
        ordering = ('order',)

class Customer(EmailRecipientMixin, models.Model):
    '''
    Not all customers choose to log in when they sign up for classes, and
    sometimes Users register their spouses, friends, or other customers.
    However, we still need to keep track of those customers' registrations.
    So, Customer objects are unique for each combination of name and email
    address, even though Users are unique by email address only.  Customers
    also store name and email information separately from the User object.
    '''
    user = models.OneToOneField(
        User, null=True, blank=True, verbose_name=_('User account'),
        on_delete=models.SET_NULL
    )

    first_name = models.CharField(_('First name'), max_length=30)
    last_name = models.CharField(_('Last name'), max_length=30)
    email = models.EmailField(_('Email address'))
    phone = models.CharField(_('Telephone'), max_length=20, null=True, blank=True)
   
    data = models.JSONField(_('Additional data'), default=dict, blank=True)

    @property
    def fullName(self):
        return ' '.join([self.first_name or '', self.last_name or ''])
    fullName.fget.short_description = _('Name')

    def __str__(self):
        return '%s: %s' % (self.fullName, self.email)

    class Meta:
        unique_together = ('last_name', 'first_name', 'email')
        ordering = ('last_name', 'first_name')
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')

