from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm

from .models import *

class LoginUserForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин или почта',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите логин или email'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите пароль'})
    )

    error_messages = {
        "invalid_login": "Неверный логин или пароль.",
        "inactive": "Этот аккаунт неактивен.",
    }

    class Meta:
        model = get_user_model()
        fields = ['username', 'password']


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Логин')
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Подтвердите пароль', widget=forms.PasswordInput())
    email = forms.CharField(label='Email')

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']
        labels = {
            'email': 'Почта',
            'first_name': 'Имя',
            'last_name': 'Фамилия'
        }

        widgets = {
            'email': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name':forms.TextInput(attrs={'class': 'form-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("Такой email уже существует")


class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(disabled=True, label='Логин',
                               widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.CharField(disabled=True, label='Почта',
                            widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'username', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия'
        }

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name':forms.TextInput(attrs={'class': 'form-input'}),
        }



class UserPasswordChange(PasswordChangeForm):
    old_password = forms.CharField(label='Старый пароль', widget=forms.PasswordInput())
    new_password1 = forms.CharField(label='Новый ароль', widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='Подтвердите новый пароль', widget=forms.PasswordInput())


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_number', 'token']  # Поля для ввода
        widgets = {
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер счета'}),
            'token': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Токен'}),
        }
        labels = {
            'account_number': 'Номер счета',
            'token': 'Токен',
        }

class SystemTokenForm(forms.ModelForm):
    class Meta:
        model = SystemToken
        fields = ['token']
        widgets = {
            'token': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите системный токен'}),
        }
        labels = {
            'token': 'Системный токен',
        }
