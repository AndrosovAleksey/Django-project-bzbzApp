from django import forms

from .functions import get_invest_info, get_token_accs_info, get_system_token

from users.models import *


class StockSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # Извлекаем stock_options из kwargs
        stock_options = kwargs.pop('stock_options', [])

        # Вызываем родительский конструктор
        super().__init__(*args, **kwargs)

        # Сохраняем stock_options как атрибут формы
        self.stock_options = stock_options
        # Добавляем поле выбора с корректными choices
        self.fields['symbol'] = forms.ChoiceField(
            choices=self.stock_options,
            label="Select a stock"
        )

class TransactionUploadForm(forms.Form):
    file = forms.FileField(label="Выберите CSV файл")

class TransactionFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата с"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата по"
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'Все категории')] + [('Категория1', 'Категория1'), ('Категория2', 'Категория2')],  # Динамически заполняется
        label="Категория"
    )

from django import forms

class InstrumentSelectionForm(forms.Form):
    stock_figi = forms.ChoiceField(
        label="Select Stock",
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    bond_figi = forms.ChoiceField(
        label="Select Bond",
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    end_date = forms.DateField(
        label="End Date",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    duration = forms.ChoiceField(
        label="Duration",
        choices=[
            ('1_hour', '1 Hour'),
            ('1_day', '1 Day'),
            ('1_week', '1 Week'),
            ('1_month', '1 Month'),
            ('1_year', '1 Year')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    granularity = forms.ChoiceField(
        label="Data Granularity",
        choices=[
            ('1', '1 Minute'),
            ('5', '5 Minutes'),
            ('15', '15 Minutes'),
            ('60', '1 Hour'),
            ('1440', '1 Day')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    selected_asset = forms.CharField(
        label="Selected Asset",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )

    def __init__(self, *args, **kwargs):
        stocks = kwargs.pop('stocks', [])
        bonds = kwargs.pop('bonds', [])
        user = kwargs.pop('user', None)  # Получаем текущего пользователя

        super().__init__(*args, **kwargs)

        # Проверяем, что пользователь передан
        if not user:
            raise ValueError("Пользователь не передан в форму.")

        token = get_system_token(user=user)

        if get_token_accs_info(token) is None:
            portfolio_figi = []
        else:
            # Извлекаем FIGI активов из портфеля
            portfolio_figi = list(get_token_accs_info(token)['figi'])

        # Разделяем акции
        owned_stocks = []
        other_stocks = []
        for s in stocks:
            if s.figi in portfolio_figi:
                owned_stocks.append((s.figi, f"{s.name} ({s.figi})"))
                continue
            other_stocks.append((s.figi, f"{s.name} ({s.figi})"))

        # Разделяем облигации
        owned_bonds = []
        other_bonds = []
        for b in bonds:
            if b.figi in portfolio_figi:
                owned_bonds.append((b.figi, f"{b.name} ({b.figi})"))
                continue
            other_bonds.append((b.figi, f"{b.name} ({b.figi})"))

        # Формируем финальные списки выбора с разделителем
        if len(portfolio_figi) == 0:
            self.fields['stock_figi'].choices = other_stocks
        else:
            self.fields['stock_figi'].choices = (
                [('', '-- Мои акции --')] +
                owned_stocks +
                [('-', '--- Другие доступные активы ---')] +  # Разделитель
                other_stocks
            )

        if len(portfolio_figi) == 0:
            self.fields['bond_figi'].choices = other_bonds
        else:
            self.fields['bond_figi'].choices = (
                [('', '-- Мои облигации --')] +
                owned_bonds +
                [('-', '--- Другие доступные активы ---')] +  # Разделитель
                other_bonds
            )

    def clean(self):
        cleaned_data = super().clean()
        stock_figi = cleaned_data.get("stock_figi")
        bond_figi = cleaned_data.get("bond_figi")
        duration = cleaned_data.get("duration")
        granularity = int(cleaned_data.get("granularity"))

        # Проверяем, что выбран только один инструмент
        if stock_figi and bond_figi:
            raise forms.ValidationError("Выберите только одну ценную бумагу (акцию или облигацию).")

        if not stock_figi and not bond_figi:
            raise forms.ValidationError("Выберите акцию или облигацию.")

        # Проверяем соответствие интервала и продолжительности
        if granularity in [1, 5, 15] and duration not in ['1_hour', '1_day']:
            raise forms.ValidationError("Интервал 1, 5 или 15 минут доступен только для продолжительности 1 часа или 1 дня.")
        if granularity == 60 and duration not in ['1_hour', '1_day', '1_week']:
            raise forms.ValidationError("Интервал 1 час доступен только для продолжительности до 1 недели.")
        if granularity == 1440 and duration not in ['1_day', '1_week', '1_month', '1_year']:
            raise forms.ValidationError("Интервал 1 день доступен только для продолжительности до 1 года.")

        return cleaned_data


class AccountSelectionForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),  # Пустой queryset (будет заполнен в представлении)
        label="Выберите счет",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем счета по текущему пользователю
        self.fields['account'].queryset = Account.objects.filter(author=user)

