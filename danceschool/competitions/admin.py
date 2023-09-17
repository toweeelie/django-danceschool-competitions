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

        if competition and competition.stage in ['d','f']:
            queryset = queryset.filter(finalist=True, comp_role=competition.comp_roles.first())

        return queryset
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'final_partner':
            try:
                # Get the parent Competition object from the request's URL parameters
                competition_id = request.resolver_match.kwargs.get('object_id')
                competition = Competition.objects.get(pk=competition_id)

                # Customize the queryset for the final_partner field
                kwargs['queryset'] = Registration.objects.filter(
                    comp_role=competition.comp_roles.last(),
                    finalist=True
                ).exclude(pk=competition.pk)  # Exclude the current registration
            except ObjectDoesNotExist:
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class JudgeInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        prelims_mj_count = {}
        finals_mj_count = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                prelims = form.cleaned_data['prelims']
                prelims_role = form.cleaned_data['prelims_role']
                prelims_main_judge = form.cleaned_data['prelims_main_judge']
                finals = form.cleaned_data['finals']
                finals_main_judge = form.cleaned_data['finals_main_judge']
                
                if prelims_role not in prelims_mj_count:
                    prelims_mj_count[prelims_role] = 0
                if prelims and prelims_main_judge:
                    prelims_mj_count[prelims_role] += 1

                if finals and finals_main_judge:
                    finals_mj_count +=1
        counts = list(prelims_mj_count.values())
        counts.append(finals_mj_count)
        for cnt in counts:
            if cnt != 1:
                raise forms.ValidationError(_('Competition should have exactly 1 main judge per role/stage.'))


class JudgeInline(admin.TabularInline):
    model = Judge
    extra = 0
    formset = JudgeInlineFormset


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title','results_visible')
    inlines = [JudgeInline,RegistrationInline]


@admin.register(PrelimsResult)
class PrelimsResultAdmin(admin.ModelAdmin):
    list_display = ('judge', 'comp_reg','result') 
    list_filter = ('judge',)


@admin.register(FinalsResult)
class FinalsResultAdmin(admin.ModelAdmin):
    list_display = ('judge', 'comp_reg','result') 
    list_filter = ('judge',)

