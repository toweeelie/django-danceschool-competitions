from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from .models import Competition,Judge,Registration,PrelimsResult,FinalsResult

class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0

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
            cnt_list = [f'{role.pluralName}:{queryset.filter(comp=competition,comp_role=role).count()}' for role in competition.comp_roles.all()]
            cnt_str = '/'.join(cnt_list)
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


class JudgeInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if len(self.forms) != 0 or self.instance.stage != 'r':
            prelims_mj_count = {}
            finals_mj_count = 0
            for form in self.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    prelims = form.cleaned_data['prelims']
                    if prelims:
                        prelims_role = form.cleaned_data['prelims_role']
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
    classes = ('collapse', )

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title','results_visible')
    inlines = [JudgeInline,RegistrationInline]
    fieldsets = (
        (None,{
            'fields':('title','stage'),
        }),
        (_('Additional settings'),{
            'classes': ('collapse', ),
            'fields':('comp_roles','finalists_number','pair_finalists','results_visible',),
        })
    )


@admin.register(PrelimsResult)
class PrelimsResultAdmin(admin.ModelAdmin):
    list_display = ('judge', 'comp_reg','result') 
    list_filter = ('judge',)


@admin.register(FinalsResult)
class FinalsResultAdmin(admin.ModelAdmin):
    list_display = ('judge', 'comp_reg','result') 
    list_filter = ('judge',)

