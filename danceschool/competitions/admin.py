from django import forms
from django.contrib import admin
from django.db import transaction
from django.http import HttpRequest,HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser

from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from PIL import Image

import segno
import unicodecsv as csv
from dal import autocomplete

from .models import Competition,Judge,Registration,PrelimsResult,FinalsResult
from .views import register_competitor


class CheckNPrintWidget(forms.CheckboxInput):
    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        if self.pk and not value:
            # Button that opens the popup
            url = reverse('registration_checkin', args=[self.pk])
            button_html = f'''
                <a href="{url}" class="related-widget-wrapper-link">
                    <span style="font-size: 18px; margin-right: 4px;">🖨️</span>
                </a>
                '''
            return mark_safe(f'{output} {button_html}')
        return mark_safe(output)
    

class RegistrationInlineForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['comp_checked_in'].widget = CheckNPrintWidget(pk=self.instance.pk)

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


def generateQR(self, request, queryset):
    
    page_width  = 100 * mm
    # Set up font sizes based on page width
    font_size_comp_name = 0.04 * page_width 
    area_for_comp_name = font_size_comp_name + 5
    qr_size = 0.3 * page_width
    area_for_qr_code = qr_size + 5
    page_height = (area_for_comp_name+area_for_qr_code)*len(queryset) + 5

    # Create a BytesIO buffer to hold the PDF data
    buffer = BytesIO()

    # Create a canvas with the specified page size
    pdf_canvas = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Register the font that supports Cyrillic characters
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf' 
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    # starting point for the first QR code section
    y_current = page_height 

    for comp in queryset:

        # get competition title
        comp_name = comp.title

        # Draw the full_name at the top of the page (centered horizontally)
        y_current -= area_for_comp_name
        pdf_canvas.setFont('DejaVuSans', font_size_comp_name)
        full_name_width = pdf_canvas.stringWidth(comp_name, 'DejaVuSans', font_size_comp_name)
        pdf_canvas.drawString((page_width - full_name_width) / 2, y_current, comp_name)

        # Draw the QR code
        y_current -= area_for_qr_code
        path = reverse('redirect_user', args=[comp.id])
        comp_url = request.build_absolute_uri(path)  

        # Generate the QR code and save it to a buffer
        qr_buffer = BytesIO()
        segno.make(comp_url).save(qr_buffer, kind='png', scale=10)
        qr_buffer.seek(0)

        # Convert the QR code buffer to PIL Image
        img = Image.open(qr_buffer)

        # Draw the QR code on the PDF   
        pdf_canvas.drawInlineImage(img, (page_width - qr_size) / 2, y_current, width=qr_size, height=qr_size)
        qr_buffer.close()


    # Finalize the PDF
    pdf_canvas.showPage()
    pdf_canvas.save()

    # Get the PDF data from the buffer
    pdf = buffer.getvalue()
    buffer.close()
    # Return the PDF as a response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="competitions.pdf"'
    return response


generateQR.short_description = _('Generate QR code links')

CompetitionAdmin.actions.append(generateQR)
