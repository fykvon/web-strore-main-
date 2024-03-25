from django.urls import path

from .views import (
    ProfileDetailView,
    ProfileUpdateView,
    ProfileOrders,
    SellerDetail,
    RegisterView,
    UserLoginView,
    UserLogoutView,
    ProfileOrderPage,
    ProfileHistoryView,
)

app_name = 'profile'

urlpatterns = [
    path('personal_account/<slug:slug>/', ProfileDetailView.as_view(), name='profile_details'),
    path('personal_account/<slug:slug>/profile_date_form/', ProfileUpdateView.as_view(), name='profile'),
    path('personal_account/<slug:slug>/history_orders/', ProfileOrders.as_view(), name='history_orders'),
    path('personal_account/<slug:slug>/history_view/', ProfileHistoryView.as_view(), name='history_view'),
    path('seller/<slug:slug>/', SellerDetail.as_view(), name='seller'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('personal_account/<slug:slug>/history_orders/detailed_order_page/<int:pk>/',
         ProfileOrderPage.as_view(), name='detailed_order'),
]
