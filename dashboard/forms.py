from django import forms
from client.models import Client, ClientAssignment
from account.models import User, Role


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


class ClientAssignmentForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Assign to CSM'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        csm_role = Role.objects.filter(name__iexact='csm').first()
        if csm_role:
            self.fields['assigned_to'].queryset = User.objects.filter(
                role=csm_role, is_active=True
            )
        else:
            self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)


class StageChangeForm(forms.Form):
    new_stage = forms.ChoiceField(
        choices=Client.STAGE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 2,
            'placeholder': 'Optional remarks...'
        })
    )
