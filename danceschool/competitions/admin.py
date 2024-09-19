from django import forms
from django.contrib import admin
from django.db import transaction
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser

import unicodecsv as csv
from dal import autocomplete

from .models import Competition,Judge,Registration,PrelimsResult,FinalsResult
from .views import register_competitor


class RegistrationInlineForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = '__all__'
        widgets = {
            'competitor': autocomplete.ModelSelect2(
                url='autocompleteCustomer',
                attrs={
                    'data-placeholder': _('Enter competitor name'),
                    'data-minimum-input-length': 1,
                    'data-max-results': 10,
                },
            )
        }


class RegistrationInline(admin.TabularInline):
    model = Registration
    form = RegistrationInlineForm
    extra = 0
    ordering = ['comp_role','comp_num']

    def get_queryset(self, request):
        try:
            # Get the parent Competition object from the request's URL parameters
            competition_id = request.resolver_match.kwargs.get('object_id')
            competition = Competition.objects.get(pk=competition_id)
        except ObjectDoesNotExist:
            competition = None

        # Customize the queryset based on the stage attribute of the Competition object
        queryset = super().get_queryset(request)

        if competition and competition.stage == 'r':
            cnt_list = [
                f'{role.pluralName}:{queryset.filter(comp=competition,comp_role=role,comp_checked_in=True).count()}/{queryset.filter(comp=competition,comp_role=role).count()}' 
                for role in competition.comp_roles.all()
            ]
            cnt_str = ';'.join(cnt_list)
            self.verbose_name_plural = f'{self.verbose_name_plural.split()[0]} ({cnt_str})' 

        if competition and competition.stage in ['d','f']:
            self.verbose_name_plural = self.verbose_name_plural.split()[0]
            queryset = queryset.filter(finalist=True, comp_role=competition.comp_roles.first())

        return queryset
    
    def get_formset(self,request,obj=None,**kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        try:
            # Get the parent Competition object from the request's URL parameters
            competition_id = request.resolver_match.kwargs.get('object_id')
            competition = Competition.objects.get(pk=competition_id)
        except ObjectDoesNotExist:
            competition = None

        if competition and competition.stage in ['d','f']:
            formset.form.base_fields['comp_num'].widget = forms.HiddenInput()
            formset.form.base_fields['competitor'].widget = forms.HiddenInput()
            formset.form.base_fields['comp_role'].widget = forms.HiddenInput()
            formset.form.base_fields['comp_checked_in'].widget = forms.HiddenInput()
            formset.form.base_fields['finalist'].widget = forms.HiddenInput()
        else:
            formset.form.base_fields['final_partner'].widget = forms.HiddenInput()
            formset.form.base_fields['final_heat_order'].widget = forms.HiddenInput()

        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'final_partner':
            try:
                # Get the parent Competition object from the request's URL parameters
                competition_id = request.resolver_match.kwargs.get('object_id')
                competition = Competition.objects.get(pk=competition_id)

                # Customize the queryset for the final_partner field
                kwargs['queryset'] = Registration.objects.filter(
                    comp=competition,
                    comp_role=competition.comp_roles.last(),
                    finalist=True
                )
            except ObjectDoesNotExist:
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class JudgeInlineForm(forms.ModelForm):
    class Meta:
        model = Judge
        fields = '__all__'
        widgets = {
            'profile': autocomplete.ModelSelect2(
                url='autocompleteUser',
                attrs={
                    'data-placeholder': _('Enter judge name'),
                    'data-minimum-input-length': 1,
                    'data-max-results': 10,
                },
            ),
            'prelims_roles' : autocomplete.Select2Multiple (
                attrs={
                    'data-placeholder': _('Roles to judge (empty for not judging prelims)'),
                    'data-max-results': 10,
                },
            )
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile'].label_from_instance = lambda obj: "%s" % obj.get_full_name()


class JudgeInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if len(self.forms) != 0 or self.instance.stage != 'r':
            prelims_mj_count = {}
            finals_mj_count = 0
            for form in self.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    for prelims_role in form.cleaned_data['prelims_roles']:
                        prelims_main_judge = form.cleaned_data['prelims_main_judge']
                    
                        if prelims_role not in prelims_mj_count:
                            prelims_mj_count[prelims_role] = 0
                        if prelims_main_judge:
                            prelims_mj_count[prelims_role] += 1
                    
                    finals = form.cleaned_data['finals']
                    finals_main_judge = form.cleaned_data['finals_main_judge']
                    if finals and finals_main_judge:
                        finals_mj_count +=1

            counts = list(prelims_mj_count.values())
            counts.append(finals_mj_count)
            for cnt in counts:
                if cnt != 1:
                    raise forms.ValidationError(_('Competition in non-registration stage should have exactly 1 main judge per role/stage.'))


class JudgeInline(admin.TabularInline):
    model = Judge
    extra = 0
    formset = JudgeInlineFormset
    form = JudgeInlineForm
    classes = ('collapse', )


class CompetitionAdminForm(forms.ModelForm):
    csv_file = forms.FileField(
        required=False,
        label=_('Import registrations from CSV file'),
        help_text=_('This field works only with existing competitions. CSV file should contain the following header:"first_name,last_name,email,comp_role". Last column should contain dance role ID\'s.')
    )
    class Meta:
        model = Competition
        fields = '__all__'
        widgets = {
            'staff': autocomplete.ModelSelect2Multiple(
                url='autocompleteStaff',
                attrs={
                    'data-placeholder': _('Enter registered user name'),
                    'data-minimum-input-length': 1,
                    'data-max-results': 10,
                },
            ),
            'comp_roles' : autocomplete.Select2Multiple (
                attrs={
                    'data-placeholder': _('Choose dance roles for competition'),
                    'data-max-results': 10,
                },
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['csv_file'].disabled = True
        self.fields['staff'].label_from_instance = lambda obj: "%s" % obj.get_full_name()

    def save(self, commit=True):
        instance = super().save(commit)
        regs_file = self.cleaned_data.get('csv_file')
        if regs_file and self.instance.id:
            request = HttpRequest()
            request.method = 'POST'
            request.user = AnonymousUser()
            for row in csv.DictReader(regs_file):
                request.POST = row
                with transaction.atomic():
                    register_competitor(request,self.instance.id)
        return instance


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    form = CompetitionAdminForm
    list_display = ('title','results_visible')
    search_fields = ('title',)
    inlines = [JudgeInline,RegistrationInline]
    fieldsets = (
        (None,{
            'fields':('title','stage'),
        }),
        (_('Additional settings'),{
            'classes': ('collapse', ),
            'fields':('staff','comp_roles','finalists_number','pair_finalists','results_visible','csv_file',),
        })
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(staff=request.user)

    def has_change_permission(self, request, obj=None):
        # Allow editing if the user is a superuser
        if request.user.is_superuser:
            return True

        # If no specific object is provided, default to checking if they can view the list
        if obj is None:
            return True

        # Allow editing if the user is the owner or a helper
        return request.user in obj.staff.all()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Only set initial data when creating a new object
            form.base_fields['staff'].initial = [request.user.id]
        return form


@admin.register(PrelimsResult)
class PrelimsResultAdmin(admin.ModelAdmin):
    list_display = ('judge', 'comp_reg','result') 
    search_fields = ('judge__profile__first_name', 'judge__profile__last_name', 'judge__comp__title', 'comp_reg__competitor__first_name', 'comp_reg__competitor__last_name')
    list_filter = ('judge',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(comp_reg__comp__staff=request.user)

    def has_change_permission(self, request, obj=None):
        # Allow editing if the user is a superuser
        if request.user.is_superuser:
            return True

        # If no specific object is provided, default to checking if they can view the list
        if obj is None:
            return True

        # Allow editing if the user is the owner or a helper
        return request.user in obj.staff.all()


@admin.register(FinalsResult)
class FinalsResultAdmin(admin.ModelAdmin):
    list_display = ('judge', 'comp_reg','result') 
    search_fields = ('judge__profile__first_name', 'judge__profile__last_name', 'judge__comp__title', 'comp_reg__competitor__first_name', 'comp_reg__competitor__last_name')
    list_filter = ('judge',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(comp_reg__comp__staff=request.user)

    def has_change_permission(self, request, obj=None):
        # Allow editing if the user is a superuser
        if request.user.is_superuser:
            return True

        # If no specific object is provided, default to checking if they can view the list
        if obj is None:
            return True

        # Allow editing if the user is the owner or a helper
        return request.user in obj.staff.all()
