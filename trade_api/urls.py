from django.urls import path
from .views import OpenPositionsView, SquareOffRuleCreateView, TradeDashboardView

urlpatterns = [
    path('', TradeDashboardView.as_view(), name='trade-dashboard'),
    path('positions/', OpenPositionsView.as_view(), name='open-positions'),
    path('rules/create/', SquareOffRuleCreateView.as_view(), name='create-squareoff-rule'),
]

