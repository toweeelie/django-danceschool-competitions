from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import DanceRole,Customer

@admin.register(DanceRole)
class DanceRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'order') 
    list_filter = ('name',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name','email') 
    search_fields = ('first_name', 'last_name','email') 
    list_filter = ('last_name',)

    # hide customers list in admin panel id user is not superuser
    def get_model_perms(self, request):
        if not request.user.is_superuser:
            return {}
        return super().get_model_perms(request)


class CustomUserAdmin(DefaultUserAdmin):
    def get_form(self, request, obj=None, **kwargs):
        """
        Override the get_form method to disable the 'is_superuser' field if the current admin user is not a superuser.
        """
        form = super().get_form(request, obj, **kwargs)

        # Check if the current user (request.user) is not a superuser
        if not request.user.is_superuser:
            form.base_fields['is_superuser'].disabled = True  # Disable the 'is_superuser' field
        
        return form

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
