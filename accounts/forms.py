from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Area

BASE_WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}


def _style(fields):
    for name, field in fields.items():
        widget = field.widget
        if name in ('password1', 'password2'):
            widget.attrs.update(BASE_WIDGET_ATTRS)
        elif isinstance(widget, forms.Select):
            widget.attrs.update(SELECT_ATTRS)
        elif isinstance(widget, forms.ClearableFileInput):
            widget.attrs.update({'class': 'form-control'})
        elif isinstance(widget, forms.CheckboxInput):
            widget.attrs.update({'class': 'form-check-input'})
        else:
            widget.attrs.update(BASE_WIDGET_ATTRS)


class OwnerUserCreateForm(UserCreationForm):
    """Owner can create a user with ANY role, and assign an Area Manager
    when the new user is a Marketing Executive."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone',
                  'employee_code', 'role', 'area', 'manager', 'profile_photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(role=User.ROLE_AREA_MANAGER)
        self.fields['manager'].required = False
        self.fields['manager'].help_text = "Only required when role is Marketing Executive."
        _style(self.fields)


class OwnerUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'employee_code',
                  'role', 'area', 'manager', 'profile_photo', 'is_active_employee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(role=User.ROLE_AREA_MANAGER)
        self.fields['manager'].required = False
        _style(self.fields)


class AreaManagerExecutiveCreateForm(UserCreationForm):
    """Area Managers can only create Marketing Executives, and the new
    user is automatically assigned to their own team."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone',
                  'employee_code', 'area', 'profile_photo']

    def __init__(self, *args, **kwargs):
        self.manager_user = kwargs.pop('manager_user', None)
        super().__init__(*args, **kwargs)
        _style(self.fields)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_MARKETING_EXECUTIVE
        user.manager = self.manager_user
        if self.manager_user and not user.area_id:
            user.area = self.manager_user.area
        if commit:
            user.save()
        return user


class AreaManagerExecutiveUpdateForm(forms.ModelForm):
    """Area Managers editing one of their own Marketing Executives — role
    and manager are fixed, not editable."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'employee_code',
                  'area', 'profile_photo', 'is_active_employee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)
