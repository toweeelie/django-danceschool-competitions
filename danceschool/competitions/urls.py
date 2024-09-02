from django.urls import path
from django.contrib import admin
from .views import SkatingCalculatorView,CompetitionListViev,redirect_user,prelims_results,finals_results,register_competitor,submit_results,registration_checkin
from .autocomplete_light_registry import UserAutoComplete,CustomerAutoComplete,StaffAutoComplete

admin.autodiscover()

urlpatterns = [
    path('skatingcalculator/', SkatingCalculatorView.as_view(), name='skatingCalculator'),
    path('skatingcalculator/init/', SkatingCalculatorView.init_tab, name='scinit'),
    path('', CompetitionListViev.as_view(), name='competitions'),
    path('<int:comp_id>/', redirect_user, name='redirect_user'),
    path('<int:comp_id>/register/', register_competitor, name='register_competitor'),
    path('<int:comp_id>/judging/', submit_results, name='submit_results'),
    path('<int:comp_id>/prelims/', prelims_results, name='prelims_results'),
    path('<int:comp_id>/finals/', finals_results, name='finals_results'),

    path('<int:reg_id>/finals/', registration_checkin, name='registration_checkin'),

    path('autocomplete/user', UserAutoComplete.as_view(), name='autocompleteUser'),
    path('autocomplete/staff', StaffAutoComplete.as_view(), name='autocompleteStaff'),
    path('autocomplete/customer', CustomerAutoComplete.as_view(create_field='fullName'), name='autocompleteCustomer'),
]
