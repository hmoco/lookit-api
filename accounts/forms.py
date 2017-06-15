from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import DemographicData, User
from guardian.shortcuts import assign_perm, get_objects_for_user, remove_perm
from studies.models import Study


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ('password', )


class UserStudiesForm(forms.Form):
    template = 'accounts/researcher_form.html'
    user = forms.ModelChoiceField(User.objects.all(), required=True, label='Researcher')
    studies = forms.ModelMultipleChoiceField(
        Study.objects.all(), required=True, label='Assigned Studies')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance')
        super(UserStudiesForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        valid = super(UserStudiesForm, self).is_valid()
        if valid and len(self.data['studies']) > 0:
            return True

    def save(self):
        permissions = ['studies.can_view', 'studies.can_edit']
        current_permitted_objects = get_objects_for_user(self.cleaned_data['user'], permissions)
        disallowed_studies = current_permitted_objects.exclude(
            id__in=[x.id for x in self.cleaned_data['studies']])

        for perm in permissions:
            for study in self.cleaned_data['studies']:
                assign_perm(perm, self.cleaned_data['user'], study)
            for study in disallowed_studies:
                remove_perm(perm, self.cleaned_data['user'], study)
        return self.cleaned_data['user']


class ParticipantSignupForm(UserCreationForm):

    def clean(self):
        cleaned_data = super(ParticipantSignupForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                'password and confirm_password do not match'
            )
        return cleaned_data

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ('username',
                  'given_name', 'middle_name', 'family_name', )
        exclude = ('user_permissions', 'groups', '_identicon', 'organization',
                   'is_active', 'is_staff', 'is_superuser', 'last_login')


class DemographicDataForm(forms.ModelForm):
    class Meta:
        model = DemographicData
        exclude = ('created_at', 'previous', 'user', 'extra', )
