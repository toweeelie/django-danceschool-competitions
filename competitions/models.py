from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

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

class Customer(models.Model):
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




class Competition(models.Model):
    '''
    Competition model
    '''

    STAGE_CHOICES = (
        ('r', 'Registration'),
        ('p', 'Prelims'),
        ('d', 'Draw'),
        ('f', 'Finals'),
    )
    title = models.CharField(
        _('Competition name'),
        max_length=200,
    )
    stage = models.CharField(max_length=12, choices=STAGE_CHOICES, default='r')
    comp_roles = models.ManyToManyField(
        DanceRole, verbose_name=_('Dance roles'),
    )
    finalists_number = models.IntegerField(
        verbose_name=_('Number of finalists per dance role'),
    )
    pair_finalists = models.BooleanField(
        _('Paired Final'), default=True, blank=True
    )
    results_visible = models.BooleanField(
        _('Publish results'), default=False, blank=False
    )

    def __str__(self):
            return self.title


class Judge(models.Model):
    '''
    Judge model
    '''
    profile = models.ForeignKey(
        User, on_delete=models.CASCADE
    )
    comp = models.ForeignKey(
        Competition, on_delete=models.CASCADE
    )
    prelims = models.BooleanField(
        _('Judging Prelims'), default=False
    )
    prelims_role = models.ForeignKey(
        DanceRole, on_delete=models.CASCADE
    )
    prelims_main_judge = models.BooleanField(
        _('Prelims Main Judge'), default=False
    )
    finals = models.BooleanField(
        _('Judging Finals'), default=False
    )
    finals_main_judge = models.BooleanField(
        _('Finals Main Judge'), default=False
    )

    def __str__(self):
        return f'{self.profile.first_name} {self.profile.last_name}'

    class Meta:
        unique_together = ('profile', 'comp')


class Registration(models.Model):
    '''
    Competitor registration record
    '''
    comp = models.ForeignKey(
        Competition, on_delete=models.CASCADE
    )
    comp_num = models.IntegerField()
    competitor = models.ForeignKey(
        Customer, verbose_name=_('Competitor'), on_delete=models.CASCADE,
    )
    comp_role = models.ForeignKey(
        DanceRole, verbose_name=_('Dance Role'), on_delete=models.CASCADE,
    )
    comp_checked_in = models.BooleanField(
        _('Checked In'), default=False, blank=False
    )
    finalist = models.BooleanField(
        _('Finalist'), default=False, blank=False
    )
    final_partner = models.ForeignKey(
        'self',verbose_name=_('Partner in final'), null=True, blank=True, on_delete=models.CASCADE,
    )
    final_heat_order = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.comp_num} {self.competitor.fullName}'

    class Meta:
        unique_together = ('comp', 'competitor')


class Result(models.Model):
    '''
    Parent result class
    '''
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    comp_reg = models.ForeignKey(Registration, on_delete=models.CASCADE)
    comment = models.CharField(max_length=100,blank=True)

    class Meta:
        abstract = True 


class PrelimsResult(Result):
    '''
    Prelims results
    '''
    JUDGE_CHOICES = (
        ('yes', 'Y'),
        ('maybe', 'Mb'),
        ('no', ''),
    )

    result = models.CharField(max_length=10, choices=JUDGE_CHOICES, default='no')
    
    class Meta:
        unique_together = ('judge', 'comp_reg')


class FinalsResult(Result):
    '''
    Finals results
    '''
    result = models.IntegerField(verbose_name=_('Place'),)

    class Meta:
        unique_together = ('judge', 'comp_reg')
        