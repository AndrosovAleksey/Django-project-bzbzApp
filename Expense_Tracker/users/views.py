from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import *

class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {'title': 'Профиль пользователя'}

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_initial(self):
        # Получаем начальные значения из текущего пользователя
        initial = super().get_initial()
        user = self.request.user
        initial['username'] = user.username
        initial['email'] = user.email
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        return initial

    def get_context_data(self, **kwargs):
        # Добавляем форму для системного токена в контекст
        context = super().get_context_data(**kwargs)
        token_instance = SystemToken.objects.first()  # Получаем текущий токен
        context['token_form'] = SystemTokenForm(instance=token_instance)
        return context

    def post(self, request, *args, **kwargs):
        # Определяем, какая форма была отправлена
        if 'profile_form_submit' in request.POST:
            # Обработка формы профиля
            form = self.get_form()
            if form.is_valid():
                form.save()
                messages.success(request, 'Профиль успешно обновлен.')
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

        elif 'token_form_submit' in request.POST:
            # Обработка формы системного токена
            token_instance = SystemToken.objects.first()
            token_form = SystemTokenForm(request.POST, instance=token_instance)
            if token_form.is_valid():
                token_form.save()
                messages.success(request, 'Системный токен успешно обновлен.')
                return redirect('users:profile')
            else:
                # Если форма токена невалидна, передаем её в контекст
                context = self.get_context_data()
                context['token_form'] = token_form
                return self.render_to_response(context)

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}

class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Регистрация'}
    success_url = reverse_lazy('users:login')

class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {'title': 'Профиль пользователя'}

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_initial(self):
        # Получаем начальные значения из текущего пользователя
        initial = super().get_initial()
        user = self.request.user
        initial['username'] = user.username
        initial['email'] = user.email
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        return initial

    def get_context_data(self, **kwargs):
        # Добавляем форму для системного токена в контекст
        context = super().get_context_data(**kwargs)
        token_instance = SystemToken.objects.filter(author=self.request.user).first()  # Получаем текущий токен
        context['token_form'] = SystemTokenForm(instance=token_instance)
        return context

    def post(self, request, *args, **kwargs):
        # Инициализируем self.object
        self.object = self.get_object()

        # Определяем, какая форма была отправлена
        if 'profile_form_submit' in request.POST:
            # Обработка формы профиля
            form = self.get_form()
            if form.is_valid():
                form.save()
                messages.success(request, 'Профиль успешно обновлен.')
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

        elif 'token_form_submit' in request.POST:
            # Обработка формы системного токена
            token_instance = SystemToken.objects.filter(author=request.user).first()
            token_form = SystemTokenForm(request.POST, instance=token_instance)
            if token_form.is_valid():
                # Удаляем старые токены перед сохранением нового
                SystemToken.objects.filter(author=request.user).delete()
                new_token = token_form.save(commit=False)
                new_token.author = request.user
                new_token.save()
                messages.success(request, 'Системный токен успешно обновлен.')
                return redirect('users:profile')
            else:
                # Если форма токена невалидна, передаем её в контекст
                context = self.get_context_data()
                context['token_form'] = token_form
                return self.render_to_response(context)

@login_required
def add_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.author = request.user  # Привязываем аккаунт к текущему пользователю
            account.save()
            messages.success(request, 'Счет успешно добавлен.')
            return redirect('users:profile')
    else:
        form = AccountForm()

    return render(request, 'users/add_account.html', {'form': form,
                                                                           'title': 'Добавить аккаунт',})

@login_required
def delete_account(request, pk):
    account = get_object_or_404(Account, pk=pk, author=request.user)
    if request.method == 'POST':
        account.delete()
        messages.success(request, 'Счет успешно удален.')
    return redirect('users:profile')

class UserPasswordChange(PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'users/password_change.html'
    extra_context = {'title': 'Смена пароля'}

    def get_success_url(self):
        return  reverse_lazy('users:password_change_done')