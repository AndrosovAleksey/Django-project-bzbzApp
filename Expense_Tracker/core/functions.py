from django.core.exceptions import ObjectDoesNotExist
from .models import *

import plotly.graph_objects as go
from plotly.offline import plot

from users.models import *

from tinkoff.invest import InstrumentStatus
import pandas as pd

from datetime import datetime, timedelta
from tinkoff.invest import Client, CandleInterval, RequestError, PortfolioResponse, PositionsResponse, PortfolioPosition

def get_available_assets(token):
    """
    Возвращает список доступных акций (тикеров) из Tinkoff Invest API.
    """
    if token is None or not isinstance(token, str):
        return None

    with Client(token) as client:
        # Получаем все акции
        shares = client.instruments.shares(
            instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE  # Только базовые инструменты
        ).instruments

        bonds = client.instruments.bonds(
            instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE  # Только базовые инструменты
        ).instruments

    return shares, bonds


# Tinkoff
def get_start_time(end_time, duration):
    """
    Вычисляет начальное время на основе продолжительности.
    """
    if duration == '1_hour':
        return end_time - timedelta(hours=1)
    elif duration == '1_day':
        return end_time - timedelta(days=1)
    elif duration == '1_week':
        return end_time - timedelta(weeks=1)
    elif duration == '1_month':
        return end_time - timedelta(days=30)  # Приближение для месяца
    elif duration == '1_year':
        return end_time - timedelta(days=365)  # Приближение для года
    else:
        raise ValueError("Неподдерживаемая продолжительность")

def get_system_token(user):
    """
    Возвращает текущий системный токен.
    Если токен не существует, возвращает None.
    """
    try:
        system_token = SystemToken.objects.filter(author=user).first()
        return system_token.token if system_token else None
    except Exception as e:
        # Обработка ошибок (например, логирование)
        print(f"Ошибка при получении системного токена: {e}")
        return None

def get_stock_data(
    figi: str,
    interval: int,
    start_time: datetime,
    end_time: datetime,
    token: str
):
    """
    Возвращает исторические данные по ценам для заданного FIGI.

    :param token: Токен Tinkoff Invest API.
    :param figi: FIGI инструмента.
    :param interval: Интервал свечей (1, 5, 15, 60, 1440 минут).
    :param start_time: Начальное время периода (datetime).
    :param end_time: Конечное время периода (datetime).
    :return: DataFrame с данными о ценах.
    """
    # Определяем интервал свечей
    if interval == 1:
        candle_interval = CandleInterval.CANDLE_INTERVAL_1_MIN
    elif interval == 5:
        candle_interval = CandleInterval.CANDLE_INTERVAL_5_MIN
    elif interval == 15:
        candle_interval = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif interval == 60:
        candle_interval = CandleInterval.CANDLE_INTERVAL_HOUR
    elif interval == 1440:
        candle_interval = CandleInterval.CANDLE_INTERVAL_DAY
    else:
        raise ValueError("Неподдерживаемый интервал")

    # Проверяем корректность временного диапазона
    if start_time >= end_time:
        raise ValueError("Начальное время не может быть больше или равно конечному времени.")

    # Получаем данные через Tinkoff Invest API
    data = []
    if get_token_accs_info(token) is None:
        return None
    with Client(token) as client:
        candles = client.market_data.get_candles(
            figi=figi,
            from_=start_time,
            to=end_time,
            interval=candle_interval
        ).candles

        if not candles:
            raise ValueError("За указанный период данных нет.")

        data = [
            {
                'time': candle.time,
                'open': cast_money(candle.open),
                'high': cast_money(candle.high),
                'low': cast_money(candle.low),
                'close': cast_money(candle.close),
                'volume': candle.volume
            }
            for candle in candles
        ]

    # Создаем DataFrame
    df = pd.DataFrame(data)
    if not df.empty:
        df['time'] = pd.to_datetime(df['time'])  # Преобразуем время в формат datetime
        return df

    # Если данных нет, возвращаем None
    return None


def cast_money(v):
    """
    Конвертирует значение MoneyValue в float.
    """
    return v.units + v.nano / 1e9



def get_start_time(end_time: datetime, duration: str) -> datetime:
    """
    Вычисляет начальное время на основе продолжительности.

    :param end_time: Конечное время периода (datetime).
    :param duration: Продолжительность ('1_hour', '1_day', '1_week', '1_month', '1_year').
    :return: Начальное время (datetime).
    """
    if duration == '1_hour':
        return end_time - timedelta(hours=1)
    elif duration == '1_day':
        return end_time - timedelta(days=1)
    elif duration == '1_week':
        return end_time - timedelta(weeks=1)
    elif duration == '1_month':
        return end_time - timedelta(days=30)  # Приближение для месяца
    elif duration == '1_year':
        return end_time - timedelta(days=365)  # Приближение для года
    else:
        raise ValueError("Неподдерживаемая продолжительность")


def get_symbol_info(symbol):
        try:
            # Загрузка данных о компании
            ticker = yf.Ticker(symbol)
            return ticker.info
        except Exception:
            # В случае ошибки возвращаем все поля как "Not Found"
            return {
                "longName": "Not Found",
                "sector": "Not Found",
                "industry": "Not Found",
                "longBusinessSummary": "Not Found",
                "country": "Not Found",
                "marketCap": "Not Found"
            }

def get_stock_candlestick(stock_data):
    if stock_data is None:
        return stock_data

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=stock_data['time'],
                high=stock_data['high'],
                low=stock_data['low'],
                open=stock_data['open'],
                close=stock_data['close'],
                increasing_line_color='#33CC99', decreasing_line_color='#FF6633'
            )
        ]
    )

    # Настройка макета графика
    fig.update_layout(
        margin=dict(l=20, r=70, t=30, b=0),  # Установка отступов (left, right, top, bottom)
        plot_bgcolor='#e7e7e7',               # Цвет фона графика
        paper_bgcolor='white',              # Цвет фона всей области графика
        yaxis_title="USD",
        xaxis=dict(showgrid=True),          # Включение сетки по оси X
        yaxis=dict(showgrid=True)           # Включение сетки по оси Y
    )
    return plot(fig, output_type='div')


# Transaction functions

def get_linegraph(x, y):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x,
                             y=y,
                             name='Expenses',
                             mode='lines+markers',
                             line=dict(color='#33CC99'),
                             marker=dict(size=10, line=dict(color='#009966', width=2)),
                             line_width=4))

    # Настройка макета графика
    fig.update_layout(
        title="Динамика расходов",
        margin=dict(l=20, r=70, t=30, b=30),  # Установка отступов (left, right, top, bottom)
        plot_bgcolor='#e7e7e7',               # Цвет фона графика
        paper_bgcolor='white',              # Цвет фона всей области графика
        yaxis_title="USD",
        xaxis=dict(showgrid=True),          # Включение сетки по оси X
        yaxis=dict(showgrid=True),           # Включение сетки по оси Y
        legend_orientation = "h",
        legend = dict(x=.5, xanchor="center"),
        hovermode = "x"
    )
    return plot(fig, output_type='div')

def get_barchart(x, y):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x,
                          y=y,
                          name='Category Count'))

    fig.update_layout(
        title="Количество категорий",
        title_x=0.5,
        margin=dict(l=20, r=70, t=30, b=30),  # Установка отступов (left, right, top, bottom)
        plot_bgcolor='#e7e7e7',               # Цвет фона графика
        paper_bgcolor='white',              # Цвет фона всей области графика
        yaxis_title="USD",
        xaxis=dict(showgrid=True),          # Включение сетки по оси X
        yaxis=dict(showgrid=True),           # Включение сетки по оси Y
        legend_orientation = "h",
        legend = dict(x=.5, xanchor="center"),
        hovermode = "x",
        colorway=['#33CC99', '#3399CC', '#6633CC', '#9933CC', '#CC33CC', '#FF3366',
                  '#FF6633', '#FF9933', '#FFCC33', '#FFFF33', '#CCFF33', '#66FF33',]
    )

    return plot(fig, output_type='div')

def get_piechart(x, y):


    fig = go.Figure()
    fig.add_trace(go.Pie(values=x,
                          labels=y,
                          name='Category Sum',
                          hole=0.7))

    fig.update_layout(
        annotations=[
            dict(text='Суммарные траты<br>'
                      'по категориям', x=0.5, y=0.5, font_size=16, showarrow=False)],
        margin=dict(l=20, r=70, t=30, b=30),  # Установка отступов (left, right, top, bottom)
        plot_bgcolor='#e7e7e7',               # Цвет фона графика
        paper_bgcolor='white',              # Цвет фона всей области графика
        yaxis_title="USD",
        xaxis=dict(showgrid=True),          # Включение сетки по оси X
        yaxis=dict(showgrid=True),           # Включение сетки по оси Y
        legend_orientation = "h",

        width=600,  # Фиксированная ширина графика
        height=500,  # Фиксированная высота графика

        showlegend=True,  # Отображение легенды
        legend=dict(
            orientation="h",  # Горизонтальная ориентация легенды
            yanchor="bottom",  # Положение легенды
            y=-0.6,  # Сдвиг легенды вниз
            xanchor="center",
            x=0.5
        ),

        hovermode = "x",
        colorway=['#33CC99', '#3399CC', '#6633CC', '#9933CC', '#CC33CC', '#FF3366',
                  '#FF6633', '#FF9933', '#FFCC33', '#FFFF33', '#CCFF33', '#66FF33',]
    )


    return plot(fig, output_type='div')


# Stock_page
# Tinkoff

def get_token_accs_info(TOKEN):

    try:
        with Client(TOKEN) as client:
            # т.к. есть валятные активы (у меня etf), то нужно их отконвертить в рубли
            # я работаю только в долл, вам возможно будут нужны и др валюты
            accounts = [acc.id for acc in client.users.get_accounts().accounts]

            portfolio_data = []
            for acc in accounts:
                data = get_invest_info(TOKEN, acc)
                data['account'] = acc
                portfolio_data.append(data)

            return pd.concat(portfolio_data)

    except RequestError as e:
        print(str(e))

def get_invest_info(TOKEN, acc_id):

    try:
        with Client(TOKEN) as client:
            # т.к. есть валятные активы (у меня etf), то нужно их отконвертить в рубли
            # я работаю только в долл, вам возможно будут нужны и др валюты
            u = client.market_data.get_last_prices(figi=['USD000UTSTOM'])
            usdrur = cast_money(u.last_prices[0].price)

            r : PortfolioResponse = client.operations.get_portfolio(account_id=acc_id)
            df = pd.DataFrame([portfolio_pose_todict(p, usdrur) for p in r.positions])

            return df

    except RequestError as e:
        print(str(e))

def portfolio_pose_todict(p : PortfolioPosition, usdrur):
    r = {
        'figi': p.figi,
        'quantity': cast_money(p.quantity),
        'expected_yield': cast_money(p.expected_yield),
        'instrument_type': p.instrument_type,
        'average_buy_price': cast_money(p.average_position_price),
        'currency': p.average_position_price.currency,
        'nkd': cast_money(p.current_nkd),
    }

    if r['currency'] == 'usd':
        # если бы expected_yield быk бы тоже MoneyValue,
        # то конвертацию валюты можно было бы вынести в cast_money
        r['expected_yield'] *= usdrur
        r['average_buy_price'] *= usdrur
        r['nkd'] *= usdrur

    r['sell_sum'] = (r['average_buy_price']*r['quantity']) + r['expected_yield'] + (r['nkd']*r['quantity'])
    r['comission'] = r['sell_sum']*0.003
    r['tax'] = r['expected_yield']*0.013 if r['expected_yield'] > 0 else 0

    return r

def get_portfolio_bars(portfolio_data):

    fig = go.Figure()
    filtered_data = portfolio_data[portfolio_data['expected_yield'] != 0.0]
    # Добавляем столбцы на график
    for i, row in filtered_data.iterrows():
        fig.add_trace(
            go.Bar(
                x=[row['figi']],
                y=[row['expected_yield']],
                name=row['figi'],
                marker=dict(
                    color='#33CC99' if row['expected_yield'] > 0 else '#FF6633',  # Цвет заливки
                    line=dict(color='#33CC99' if row['expected_yield'] > 0 else '#FF6633', width=2),  # Обводка
                    opacity=0.7  # Прозрачность
                ),
                text=f"{row['figi']}",
                hovertemplate=(
                    "<b>Name:</b> %{customdata[0]}<br>"  # Название актива
                    "<b>Change:</b> %{y:.2f} %{customdata[1]}<extra></extra>"  # Изменение и валюта
                ),
                customdata=[[row['name'], row['currency']]]  # Передаем дополнительные данные
            )
        )
    # Настройка линии нуля посередине
    fig.update_layout(
        title="Текущие Потери/Доходы",
        title_x = 0.06,
        title_y = 0.88,
        plot_bgcolor='#e7e7e7',  # Цвет фона графика
        paper_bgcolor='white',  # Цвет фона всей области графика
        height = 600,
        yaxis=dict(
            zeroline=True,  # Линия нуля
            zerolinecolor="black",  # Цвет линии нуля
            zerolinewidth=2,  # Толщина линии нуля
            automargin=True
        ),
        showlegend=False,  # Убираем легенду
        margin=dict(l=70, r=70, t=100, b=30),  # Увеличиваем нижний отступ для подписей
        xaxis=dict(automargin=True),  # Автоматический отступ для подписей по оси X
        xaxis_visible=False,
    )

    return plot(fig, output_type='div')

def find_name(figi):
    try:
        # Сначала ищем в таблице Stock
        stock = Stock.objects.get(figi=figi)
        return stock.name  # Возвращаем название акции
    except ObjectDoesNotExist:
        try:
            # Если не нашли в таблице Stock, ищем в таблице Bond
            bond = Bond.objects.get(figi=figi)
            return bond.name  # Возвращаем название облигации
        except ObjectDoesNotExist:
            return "Unknown"  # Если не нашли ни в одной таблице, возвращаем "Unknown"

