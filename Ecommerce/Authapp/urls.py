from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register_view, name='register'),
    path('otp-verify/', otp_verify_view, name='otp_verify'),
    path('login/', login_view, name='login'),
    path('', home_view, name='home'),
    path('logout', logout_view, name='logout'),
    path("category/<slug:subcategory_slug>/", category_view, name="category_view"),
    path('product/<int:pk>/', product_detail_view, name="product_detail"),
    path('cart/', cart_view, name="cart_view"),
    path('add-to-cart/<int:product_id>/', add_to_cart, name="add_to_cart"),
    path('update_cart/<int:item_id>/', update_cart, name='update_cart'),
    path('remove-from-cart/<int:cart_id>/', remove_from_cart, name="remove_from_cart"),
    path("wishlist/", wishlist_view, name="wishlist"),
    path("wishlist/add/<int:product_id>/", add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/remove/<int:product_id>/", remove_from_wishlist, name="remove_from_wishlist"),
    path("wishlist/move_to_cart/<int:product_id>/", move_to_cart, name="move_to_cart"),
    path('cart/move_to_wishlist/<int:product_id>/', move_to_wishlist, name='move_to_wishlist'),
    path("checkout/", checkout_view, name="checkout"),
    path('order-confirmation/<str:order_id>/', order_confirmation_view, name='order_confirmation'),
    path('razorpay-payment/<str:order_id>/', razorpay_payment_view, name='razorpay_payment'),
    path("razorpay-success/", razorpay_success_view, name="razorpay_success"),
    path('profile/', profile_update_view, name='profile'),
    path('my-orders/', order_list_view, name='order_list'),  # Order listing with filter
    path('my-orders/<str:order_id>/', order_detail_view, name='order_detail'),  # Order detail view
    path("order/<str:order_id>/invoice/", generate_invoice, name="generate_invoice"),
    path("contact-us/", contact_us, name="contact_us"),
    path('about/', about, name='about'),
    
]


