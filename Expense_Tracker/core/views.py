from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView, DeleteView
from django_plotly_dash.access import login_required

from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from .models import Stock, Bond
from .forms import InstrumentSelectionForm
from .functions import get_stock_data, get_stock_candlestick
from datetime import datetime, timedelta

from .functions import *
from django.shortcuts import render, redirect
from .models import StockInfo
from .forms import StockSelectionForm
from datetime import datetime, timedelta
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

import csv
from io import TextIOWrapper
import pandas as pd
from .models import Transaction
from .forms import TransactionFilterForm, TransactionUploadForm
from .functions import get_linegraph, get_piechart, get_barchart

from users.models import *

# Start Page
def startPage(request):
    content = {'title': 'Start'}
    return render(request, 'core/start.html', content)

# Stock Page

class StocksView(LoginRequiredMixin, FormView):
    template_name = 'core/stocks_graphs.html'
    form_class = InstrumentSelectionForm
    success_url = reverse_lazy('stocks_view')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['stocks'] = Stock.objects.all()
        kwargs['bonds'] = Bond.objects.all()
        kwargs['user'] = self.request.user  # Передаем текущего пользователя
        return kwargs

    def form_valid(self, form):
        # Получаем данные из формы
        stock_figi = form.cleaned_data.get('stock_figi')
        bond_figi = form.cleaned_data.get('bond_figi')
        end_date = form.cleaned_data.get('end_date')
        duration = form.cleaned_data.get('duration')
        granularity = int(form.cleaned_data.get('granularity'))

        # Определяем выбранный инструмент
        if stock_figi:
            instrument = Stock.objects.get(figi=stock_figi)
            figi = stock_figi
            instrument_type = "Stock"
        elif bond_figi:
            instrument = Bond.objects.get(figi=bond_figi)
            figi = bond_figi
            instrument_type = "Bond"

        try:
            # Вычисляем start_time
            end_time = datetime.combine(end_date, datetime.min.time())
            start_time = get_start_time(end_time, duration)

            # Получаем данные о графике
            token = get_system_token(self.request.user)  # Получаем токен текущего пользователя
            stock_data = get_stock_data(token=token, figi=instrument.figi, interval=granularity, start_time=start_time, end_time=end_time)

            # Если данные отсутствуют, выводим сообщение об ошибке
            if stock_data is None:
                form.add_error(None, "Не удалось получить данные о котировках. Проверьте системный токен в вашем профиле.")
                return self.form_invalid(form)

            # Создаем график свечей
            fig_div = get_stock_candlestick(stock_data)

            # Передаем данные в контекст
            context = {
                'symbol': instrument.ticker,
                'end_day': end_date,
                'field_name': f'{instrument.name} ({figi})',
                'stock_candlestick': fig_div,
                'instrument_name': instrument.name,
                'instrument_type': instrument_type,
                'currency': instrument.currency,
                'sector': getattr(instrument, 'sector', 'N/A'),
                'exchange': instrument.exchange,
                'nominal': instrument.nominal,
                'form': form,
                'title': 'Котировки',
            }

            return render(self.request, self.template_name, context)

        except ValueError as e:
            # Если данных нет, передаем сообщение об ошибке
            form.add_error(None, str(e))
            return self.form_invalid(form)


# Transaction page
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'core/combined.html'  # Новый объединенный шаблон
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(author=self.request.user)

        # Фильтрация по параметрам GET-запроса
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        category = self.request.GET.get('category')

        if start_date:
            queryset = queryset.filter(operation_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(operation_date__lte=end_date)
        if category:
            queryset = queryset.filter(category=category)

        queryset = queryset.order_by('-operation_date')  # Сортировка по убыванию даты
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Формы фильтрации и загрузки
        context['filter_form'] = TransactionFilterForm(self.request.GET)
        context['upload_form'] = TransactionUploadForm()

        # Уникальные категории для текущего пользователя
        context['categories'] = (
            Transaction.objects
            .filter(author=self.request.user)
            .values_list('category', flat=True)
            .distinct()
        )

        # Если данные есть, генерируем графики
        if self.get_queryset().exists():
            # Импортируем данные
            expenses = self.get_queryset()

            # Преобразуем данные в DataFrame
            data = {
                'Дата': [expense.operation_date for expense in expenses],
                'Сумма': [expense.amount for expense in expenses],
                'Категория': [expense.category for expense in expenses],
            }
            df = pd.DataFrame(data)
            df['Дата'] = pd.to_datetime(pd.to_datetime(df['Дата']).dt.strftime("%Y-%m-%d"))

            # Применяем фильтры из GET-параметров
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')
            category = self.request.GET.get('category')

            if start_date:
                df = df[df['Дата'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['Дата'] <= pd.to_datetime(end_date)]
            if category:
                df = df[df['Категория'] == category]

            # Группировка по дням
            df_by_day = df[df['Сумма'] < 0].groupby('Дата')[['Сумма']].sum().apply(lambda x: x * -1)

            # Создание полного диапазона дат
            all_dates = pd.date_range(start=df['Дата'].min(), end=df['Дата'].max())
            full_date_df = pd.DataFrame(index=all_dates, columns=['Сумма']).fillna(0)
            result_df = full_date_df.add(df_by_day, fill_value=0).reset_index().rename(columns={'index': 'Дата'})

            # Группировка по месяцам
            df_by_day = result_df.set_index('Дата')['Сумма']
            df_by_month = result_df.set_index('Дата')['Сумма'].resample('1ME').sum()

            # Графики по дням и месяцам
            daily_fig1_div = get_linegraph(df_by_day.index, df_by_day.values)
            monthly_fig1_div = get_linegraph(df_by_month.index, df_by_month.values)

            # Остальные графики
            df_by_category = df.groupby('Категория')[['Дата', 'Сумма']].count().sort_values(by='Сумма', ascending=False)
            df_by_category_sum = df[df['Сумма'] < 0].groupby('Категория')[['Сумма']].sum().apply(abs)

            fig2_div = get_piechart(df_by_category_sum['Сумма'].values, df_by_category_sum.index)
            fig3_div = get_barchart(df_by_category.index, df_by_category['Сумма'])

            # Передаем данные в контекст
            context['daily_fig1'] = daily_fig1_div
            context['monthly_fig1'] = monthly_fig1_div
            context['fig2'] = fig2_div
            context['fig3'] = fig3_div
            context['title'] = 'Мои расходы'

        return context


class TransactionUploadView(LoginRequiredMixin, FormView):
    template_name = 'core/transaction_list.html'
    form_class = TransactionUploadForm
    success_url = reverse_lazy('transaction_list')

    def get_context_data(self, **kwargs):
        kwargs['upload_form'] = kwargs.pop('form')
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        uploaded_file = self.request.FILES['file']

        # Проверяем, что файл имеет расширение CSV
        if not uploaded_file.name.endswith('.csv'):
            form.add_error('file', 'Файл должен быть в формате CSV')
            return self.form_invalid(form)

        try:
            decoded_file = TextIOWrapper(uploaded_file, encoding='utf-8')
            reader = csv.reader(decoded_file)
            next(reader)  # Пропускаем заголовок

            transactions = []
            for row in reader:
                if len(row) < 8:
                    continue  # Пропускаем некорректные строки

                operation_date = datetime.strptime(row[0], '%d.%m.%Y %H:%M:%S').date()
                card_number = row[1]
                currency = row[2]
                if row[3]:
                    category = row[3]
                else:
                    category = 'Другое'
                mcc = row[4]
                description = row[5]
                bonuses = float(row[6].replace(',', '')) if row[6] else 0
                amount = float(row[7].replace(',', ''))

                transaction = Transaction(
                    operation_date=operation_date,
                    card_number=card_number,
                    currency=currency,
                    category=category,
                    mcc=mcc,
                    description=description,
                    bonuses=bonuses,
                    amount=amount,
                    author = self.request.user
                )
                transactions.append(transaction)

            Transaction.objects.bulk_create(transactions)
        except Exception as e:
            form.add_error(None, f'Ошибка при обработке файла: {str(e)}')
            return self.form_invalid(form)

        return super().form_valid(form)


class TransactionDeleteAllView(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy('transaction_list')

    def post(self, request, *args, **kwargs):
        Transaction.objects.all().delete()
        return redirect(self.success_url)


class TransactionDeleteView(DeleteView):
    success_url = reverse_lazy('transaction_list')

    def post(self, request, *args, **kwargs):
        transaction_id = kwargs.get('pk')
        Transaction.objects.filter(id=transaction_id).delete()
        return redirect(self.success_url)



# Stocks_bag page
from django.shortcuts import render
import plotly.express as px
from .functions import get_invest_info

@login_required
def portfolio_view(request):
    # Инициализация переменных
    token = None
    account_id = None
    error = None
    table_data = None
    chart_html = None

    # Получаем выбранный аккаунт из GET-параметров
    selected_account_id = request.GET.get('account')
    if selected_account_id:
        try:
            # Находим аккаунт по ID
            selected_account = Account.objects.get(id=selected_account_id, author=request.user)
            token = selected_account.token
            account_id = selected_account.account_number
        except Account.DoesNotExist:
            error = "Выбранный аккаунт не найден."

    # Если аккаунт и токен выбраны, получаем данные портфеля
    if token and account_id:
        try:
            # Получаем данные о портфеле
            portfolio_data = get_invest_info(token, account_id)

            # Добавляем столбец 'name' в DataFrame
            df = portfolio_data
            df['name'] = df['figi'].apply(find_name)

            # Тестовые изменения (примеры модификации данных)
            df.loc[df.shape[0]] = df.loc[0]
            df.at[df.shape[0] - 1, 'figi'] = 'adadaddad'
            df.at[df.shape[0] - 1, 'expected_yield'] = -1 * df.at[df.shape[0] - 1, 'expected_yield']

            df.loc[df.shape[0]] = df.loc[0]
            df.at[df.shape[0] - 1, 'figi'] = 'dcdvdvdvdv'
            df.at[df.shape[0] - 1, 'expected_yield'] = -1 * df.at[df.shape[0] - 1, 'expected_yield'] - 1000
            df.at[df.shape[0] - 1, 'currency'] = 'usd'

            df.loc[df.shape[0]] = df.loc[0]
            df.at[df.shape[0] - 1, 'figi'] = 'adadavvdac'
            df.at[df.shape[0] - 1, 'expected_yield'] = -1 * df.at[df.shape[0] - 1, 'expected_yield'] + 1000

            df.loc[df.shape[0]] = df.loc[0]
            df.at[df.shape[0] - 1, 'figi'] = 'vddffadada'
            df.at[df.shape[0] - 1, 'expected_yield'] = 1 * df.at[df.shape[0] - 1, 'expected_yield'] + 27

            # Преобразуем DataFrame в список словарей
            table_data = df.to_dict(orient='records')

            # Создаем график с помощью plotly.graph_objects
            chart_html = get_portfolio_bars(portfolio_data)

        except Exception as e:
            error = f"Ошибка при получении данных портфеля: {str(e)}"

    # Получаем все аккаунты пользователя для выпадающего списка
    accounts = Account.objects.filter(author=request.user)

    context = {
        'accounts': accounts,
        'table_data': table_data,
        'chart_html': chart_html,
        'error': error,
        'title': 'Мой портфель',
    }

    return render(request, 'core/stocks_bag.html', context)

