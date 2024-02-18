from django.urls import path, include
from django.apps import apps


urlpatterns = [
    # For better authentication
    path('accounts/', include('allauth.urls')),
    # The URLS associated with all built-in core functionality.
    #path('', include('danceschool.core.urls')),
]

# If additional danceschool apps are installed, automatically add those URLs as well.
if apps.is_installed('danceschool.competitions'):
    urlpatterns.append(path('competitions/', include('danceschool.competitions.urls')),)
