from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import ForeignKey


class StockInfo(models.Model):
    symbol = models.CharField(max_length=10, unique=True, verbose_name="Тикер")
    company_name = models.CharField(max_length=255, verbose_name="Название компании")
    sector = models.CharField(max_length=100, blank=True, null=True, verbose_name="Сектор")
    industry = models.CharField(max_length=100, blank=True, null=True, verbose_name="Отрасль")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name="Страна")
    market_cap = models.FloatField(blank=True, null=True, verbose_name="Капитализация рынка")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"

class Transaction(models.Model):
    operation_date = models.DateField(verbose_name="Дата операции")
    card_number = models.CharField(max_length=16, blank=True, verbose_name="Номер карты")
    currency = models.CharField(max_length=3, verbose_name="Валюта")
    category = models.CharField(max_length=50, blank=True, verbose_name="Категория")
    mcc = models.CharField(max_length=4, blank=True, verbose_name="MCC")
    description = models.TextField(verbose_name="Описание")
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Бонусы")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")

    author = ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='posts', null=False, default=None)

    def __str__(self):
        return f"{self.operation_date} - {self.description}"


from django.db import models

class Stock(models.Model):
    figi = models.CharField(max_length=12, unique=True, verbose_name="FIGI")
    ticker = models.CharField(max_length=10, verbose_name="Тикер")
    name = models.CharField(max_length=255, verbose_name="Название компании")
    currency = models.CharField(max_length=3, verbose_name="Валюта")
    sector = models.CharField(max_length=100, blank=True, null=True, verbose_name="Сектор")
    country_of_risk = models.CharField(max_length=2, verbose_name="Код страны риска")
    country_of_risk_name = models.CharField(max_length=100, verbose_name="Страна риска")
    exchange = models.CharField(max_length=50, verbose_name="Торговая площадка")
    lot = models.IntegerField(verbose_name="Лотность")
    nominal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Номинал")
    trading_status = models.CharField(max_length=50, verbose_name="Режим торгов")
    ipo_date = models.DateField(blank=True, null=True, verbose_name="Дата IPO")

    def __str__(self):
        return f"{self.ticker} - {self.name}"

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"


class Bond(models.Model):
    figi = models.CharField(max_length=12, unique=True, verbose_name="FIGI")
    ticker = models.CharField(max_length=10, verbose_name="Тикер")
    name = models.CharField(max_length=255, verbose_name="Название облигации")
    currency = models.CharField(max_length=3, verbose_name="Валюта")
    maturity_date = models.DateField(verbose_name="Дата погашения")
    nominal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Номинал")
    coupon_quantity_per_year = models.IntegerField(verbose_name="Количество купонов в год")
    floating_coupon_flag = models.BooleanField(default=False, verbose_name="Плавающий купон")
    perpetual_flag = models.BooleanField(default=False, verbose_name="Бессрочная облигация")
    amortization_flag = models.BooleanField(default=False, verbose_name="Амортизация долга")
    exchange = models.CharField(max_length=50, verbose_name="Торговая площадка")
    trading_status = models.CharField(max_length=50, verbose_name="Режим торгов")

    def __str__(self):
        return f"{self.ticker} - {self.name}"

    class Meta:
        verbose_name = "Облигация"
        verbose_name_plural = "Облигации"


from django.db import models
