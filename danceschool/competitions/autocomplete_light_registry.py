from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from danceschool.core.models import Customer

from dal import autocomplete

class UserAutoComplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = User.objects.all()

        if self.q:
            words = self.q.split(' ')
            lastName = words.pop()
            firstName = words.pop() if words else lastName

            qs = qs.filter(
                Q(first_name__istartswith=firstName) | Q(last_name__istartswith=lastName) |
                Q(email__istartswith=self.q)
            )

        return qs

    def get_result_label(self, result):
        return "%s" % result.get_full_name()

class StaffAutoComplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = User.objects.filter(is_staff=True)

        if self.q:
            words = self.q.split(' ')
            lastName = words.pop()
            firstName = words.pop() if words else lastName

            qs = qs.filter(
                Q(first_name__istartswith=firstName) | Q(last_name__istartswith=lastName) |
                Q(email__istartswith=self.q)
            )

        return qs

    def get_result_label(self, result):
        return "%s" % result.get_full_name()

class CustomerAutoComplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Customer.objects.all()

        if self.q:
            words = self.q.split(' ')
            lastName = words.pop()
            firstName = words.pop() if words else lastName

            qs = qs.filter(
                Q(first_name__istartswith=firstName) | Q(last_name__istartswith=lastName) |
                Q(email__istartswith=self.q)
            )

        return qs

    def create_object(self, text):
        ''' Allow creation of new customers using a full name string. '''
        if self.create_field == 'fullName':
            words = text.split(' ')
            firstName = words[0]
            if '@' in words[-1]:
                lastName = ' '.join(words[1:-1])
                email = words[-1]
            else:
                lastName = ' '.join(words[1:])
                email = 'noemail@example.com'
            return self.get_queryset().create(**{'first_name': firstName, 'last_name': lastName, 'email': email})
        else:
            return super().create_object(text)
