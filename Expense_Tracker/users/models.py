from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import ForeignKey

class Account(models.Model):
    account_number = models.CharField(max_length=20, unique=False, verbose_name="Номер счета")
    token = models.CharField(max_length=128, unique=False, verbose_name="Токен")

    author = ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='accounts', null=False, default=None)

    def __str__(self):
        return f"Счет {self.account_number} (Пользователь: {self.author.username})"

    class Meta:
        verbose_name = "Счет"
        verbose_name_plural = "Счета"


class SystemToken(models.Model):
    token = models.CharField(max_length=255, unique=False, verbose_name="Системный токен")
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='system_tokens',null=False, default=None)

    def __str__(self):
        return f"Токен {self.token} (Пользователь: {self.author.username})"

    class Meta:
        verbose_name = "Системный токен"
        verbose_name_plural = "Системные токены"