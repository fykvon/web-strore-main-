from django.urls import path

from .views import (
    AddProductToCartView,
    AddProductView,
    TakeProductView,
    CartListView,
    DeleteProductFromCartView,
    ClearCartView
)

app_name = 'cart'

urlpatterns = [
    path('', CartListView.as_view(), name='index'),
    path('<int:offer_id>/', AddProductToCartView.as_view(), name='add_product_to_cart'),
    path('add_product/<slug:slug>/', AddProductView.as_view(), name='add_product'),
    path('take_product/<slug:slug>/', TakeProductView.as_view(), name='take_product'),
    path('delete_product/<slug:slug>/', DeleteProductFromCartView.as_view(), name='delete_product'),
    path('cart/clear/', ClearCartView.as_view(), name='cart_clear'),
]
