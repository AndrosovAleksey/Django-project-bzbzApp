from django.urls import path
from .views import *

urlpatterns = [
    path('', startPage, name='home'),
    path('stocks/', StocksView.as_view(), name='stocks_graphs'),
    path('stocks_bag/', portfolio_view, name='stocks_bag'),
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/upload/', TransactionUploadView.as_view(), name='upload_transactions'),
    path('transactions/delete-all/', TransactionDeleteAllView.as_view(), name='delete_all_transactions'),
    path('transactions/delete/<int:pk>/', TransactionDeleteView.as_view(), name='delete_transaction'),
]