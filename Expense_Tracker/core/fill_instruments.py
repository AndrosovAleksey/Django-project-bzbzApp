from django.core.management.base import BaseCommand
from tinkoff.invest import Client, InstrumentStatus
from .models import Stock, Bond
from datetime import datetime

def cast_money(v):
    """
    Конвертирует значение MoneyValue в float.
    """
    return v.units + v.nano / 1e9

class Command(BaseCommand):
    help = "Заполняет базу данных информацией о акциях и облигациях из Tinkoff Invest API."

    def handle(self, *args, **kwargs):
        token = "t.NfGmTwiebOApFnvP7-2gTlZksUi4Ga8XU17YTx4MliipF5F2suEEkAo0-FF2aaWcUSo3r3Rs8TosVbfayW7wlg"  # Замените на ваш токен

        with Client(token) as client:
            # Получаем акции
            shares = client.instruments.shares(
                instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE
            ).instruments

            for share in shares:
                # Проверяем тип ipo_date
                ipo_date = share.ipo_date.ToDatetime() if hasattr(share.ipo_date, 'ToDatetime') else share.ipo_date

                Stock.objects.update_or_create(
                    figi=share.figi,
                    defaults={
                        "ticker": share.ticker,
                        "name": share.name,
                        "currency": share.currency,
                        "sector": share.sector or "N/A",
                        "country_of_risk": share.country_of_risk,
                        "country_of_risk_name": share.country_of_risk_name,
                        "exchange": share.exchange,
                        "lot": share.lot,
                        "nominal": cast_money(share.nominal) if share.nominal else None,
                        "trading_status": share.trading_status,
                        "ipo_date": ipo_date,  # Используем преобразованное значение
                    },
                )
                self.stdout.write(f"Добавлена/обновлена акция: {share.ticker} - {share.name}")

            # Получаем облигации
            bonds = client.instruments.bonds(
                instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE
            ).instruments

            for bond in bonds:
                # Проверяем тип maturity_date
                maturity_date = bond.maturity_date.ToDatetime() if hasattr(bond.maturity_date, 'ToDatetime') else bond.maturity_date

                Bond.objects.update_or_create(
                    figi=bond.figi,
                    defaults={
                        "ticker": bond.ticker,
                        "name": bond.name,
                        "currency": bond.currency,
                        "maturity_date": maturity_date,  # Используем преобразованное значение
                        "nominal": cast_money(bond.nominal),
                        "coupon_quantity_per_year": bond.coupon_quantity_per_year,
                        "floating_coupon_flag": bond.floating_coupon_flag,
                        "perpetual_flag": bond.perpetual_flag,
                        "amortization_flag": bond.amortization_flag,
                        "exchange": bond.exchange,
                        "trading_status": bond.trading_status,
                    },
                )
                self.stdout.write(f"Добавлена/обновлена облигация: {bond.ticker} - {bond.name}")