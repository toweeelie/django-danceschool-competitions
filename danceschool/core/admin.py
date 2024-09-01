from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

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
