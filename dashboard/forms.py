from django import forms
from client.models import Client


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )


class StageChangeForm(forms.Form):
    new_stage = forms.ChoiceField(
        choices=Client.STAGE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
