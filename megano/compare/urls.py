from django.urls import path

from compare.views import (AddToComparisonView,
                           ComparisonView,
                           ComparisonErrorView,
                           ComparisonNoneView,
                           ClearComparisonView,
                           )

app_name = 'compare'

urlpatterns = [
    path('add-to-comparison/<int:product_id>/', AddToComparisonView.as_view(), name='add_to_comparison'),
    path('clear_comparison/', ClearComparisonView.as_view(), name='clear_comparison'),
    path('comparison/', ComparisonView.as_view(), name='comparison'),
    path('comparison-error/', ComparisonErrorView.as_view(), name='comparison_error'),
    path('comparison-none/', ComparisonNoneView.as_view(), name='comparison_none'),
]
