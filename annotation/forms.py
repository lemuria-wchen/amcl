from django import forms
from .models import UserProfile


class UserLoginForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = UserProfile
        fields = ['username', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


class UserRegisterForm(forms.ModelForm):
    repeated_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = UserProfile
        fields = [
            'email', 'student_id', 'username', 'name',
            'phone_number', 'gender', 'education', 'school', 'password'
        ]
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


class PasswordForgetForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['email']
        widgets = {
            'email': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PasswordResetForm(forms.ModelForm):
    repeated_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['password']
        widgets = {
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
