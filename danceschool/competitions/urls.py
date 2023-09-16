from django.urls import path
from django.contrib import admin
from .views import SkatingCalculatorView,CompetitionListViev,redirect_user,prelims_results,finals_results,register_competitor,submit_results

admin.autodiscover()

urlpatterns = [
    path('skatingcalculator/', SkatingCalculatorView.as_view(), name='skatingCalculator'),
    path('skatingcalculator/init/', SkatingCalculatorView.init_tab, name='scinit'),
    path('competitions/', CompetitionListViev.as_view(), name='competitions'),
    path('competitions/<int:comp_id>/', redirect_user, name='redirect_user'),
    path('competitions/<int:comp_id>/register/', register_competitor, name='register_competitor'),
    path('competitions/<int:comp_id>/judging/', submit_results, name='submit_results'),
    path('competitions/<int:comp_id>/prelims/', prelims_results, name='prelims_results'),
    path('competitions/<int:comp_id>/finals/', finals_results, name='finals_results'),
]
